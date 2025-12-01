#!/usr/bin/env python3
"""
Script para generar reglas de Suricata automáticamente usando OpenAI.
Analiza eventos de Suricata (eve.json) y genera reglas basadas en patrones detectados.
"""

import json
import argparse
import os
import subprocess
import sys
from typing import Optional

try:
    from openai import OpenAI  # type: ignore
except ImportError:
    print("[ERROR] La biblioteca 'openai' no está instalada.")
    print("[INFO] Instálala con: pip install openai")
    sys.exit(1)


# Configuración
DEFAULT_RULES_PATH = "/etc/suricata/rules/generated.rules"
OPENAI_MODEL = "gpt-4o-mini"  # Usando modelo disponible (gpt-4.1 no existe aún)
PROMPT_TEMPLATE = """Analiza el archivo JSON adjunto generado por Suricata (eve.json).

Identifica patrones de cryptojacking, minería o tráfico sospechoso.

Genera reglas de Suricata basadas en los patrones presentes.

Usa content:, pcre:, flow:, flowbits:, o patrones de red específicos.

No inventes datos. Usa únicamente información observable en el JSON.

Devuelve solo reglas y comentarios explicativos.

Formato de salida esperado:
# Comentario explicativo
alert <protocol> <source_ip> <source_port> -> <dest_ip> <dest_port> (msg:"..."; content:"..."; sid:...; rev:1;)
"""


def filter_events(
    input_file: str,
    output_file: str,
    ip: Optional[str] = None,
    port: Optional[int] = None,
    flow_id: Optional[str] = None
) -> int:
    """
    Filtra eventos de eve.json según los criterios especificados.
    
    Args:
        input_file: Ruta al archivo eve.json
        output_file: Ruta donde guardar el JSON filtrado
        ip: IP a filtrar (puede ser src_ip o dest_ip)
        port: Puerto a filtrar (puede ser src_port o dest_port)
        flow_id: Flow ID a filtrar
    
    Returns:
        Número de eventos filtrados
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"El archivo {input_file} no existe.")
    
    filtered_events = []
    
    print(f"[INFO] Leyendo eventos de {input_file}...")
    
    # Leer archivo JSON (puede ser JSONL - una línea por evento)
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # Intentar leer como JSON array primero
            try:
                events = json.load(f)
                if not isinstance(events, list):
                    events = [events]
            except json.JSONDecodeError:
                # Si falla, intentar como JSONL (una línea por evento)
                f.seek(0)
                events = []
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        raise ValueError(f"Error al leer el archivo JSON: {e}")
    
    print(f"[INFO] Total de eventos en el archivo: {len(events)}")
    
    # Filtrar eventos
    for event in events:
        match = False
        
        # Filtrar por IP (src_ip o dest_ip)
        if ip:
            src_ip = event.get('src_ip') or event.get('source_ip') or ''
            dest_ip = event.get('dest_ip') or event.get('destination_ip') or ''
            if ip in src_ip or ip in dest_ip:
                match = True
        
        # Filtrar por puerto (src_port o dest_port)
        if port is not None:
            src_port = event.get('src_port') or event.get('source_port')
            dest_port = event.get('dest_port') or event.get('destination_port')
            if src_port == port or dest_port == port:
                match = True
        
        # Filtrar por flow_id
        if flow_id:
            event_flow_id = event.get('flow_id') or event.get('flow', {}).get('id')
            if str(event_flow_id) == str(flow_id):
                match = True
        
        # Si no hay filtros, incluir todos (pero esto no debería pasar por validación)
        if not ip and port is None and not flow_id:
            match = True
        
        if match:
            filtered_events.append(event)
    
    # Guardar eventos filtrados
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_events, f, indent=2, ensure_ascii=False)
    
    print(f"[INFO] Eventos filtrados guardados en {output_file}: {len(filtered_events)} eventos")
    
    return len(filtered_events)


def upload_to_openai(file_path: str, api_key: str) -> str:
    """
    Sube un archivo a OpenAI usando la API de Files.
    
    Args:
        file_path: Ruta al archivo a subir
        api_key: API key de OpenAI
    
    Returns:
        ID del archivo subido
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo {file_path} no existe.")
    
    client = OpenAI(api_key=api_key)
    
    print(f"[INFO] Subiendo {file_path} a OpenAI...")
    
    try:
        with open(file_path, 'rb') as f:
            file_response = client.files.create(
                file=f,
                purpose='assistants'
            )
        
        file_id = file_response.id
        print(f"[INFO] Archivo subido exitosamente. File ID: {file_id}")
        
        return file_id
    
    except Exception as e:
        raise RuntimeError(f"Error al subir archivo a OpenAI: {e}")


def generate_rules(file_id: str, api_key: str, file_path: str) -> str:
    """
    Genera reglas de Suricata usando OpenAI basándose en el archivo subido.
    
    Args:
        file_id: ID del archivo subido a OpenAI
        api_key: API key de OpenAI
        file_path: Ruta al archivo JSON (para leer contenido si es necesario)
    
    Returns:
        Reglas de Suricata generadas
    """
    client = OpenAI(api_key=api_key)
    
    print("[INFO] Generando reglas con OpenAI...")
    
    try:
        # Leer contenido del archivo para incluirlo en el prompt
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Limitar el tamaño del contenido si es muy grande (primeros 10000 caracteres)
        if len(file_content) > 10000:
            file_content = file_content[:10000] + "\n... (contenido truncado)"
        
        # Crear prompt completo con el contenido del archivo
        full_prompt = f"""{PROMPT_TEMPLATE}

Contenido del archivo JSON a analizar:
```json
{file_content}
```
"""
        
        # Crear mensaje con el archivo adjunto
        # Intentar usar file_ids si está disponible, sino usar solo el contenido
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en reglas de Suricata y detección de amenazas de red."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
        except TypeError:
            # Si file_ids no está disponible, usar solo el contenido en el prompt
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en reglas de Suricata y detección de amenazas de red."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
        
        rules = response.choices[0].message.content
        
        if not rules or len(rules.strip()) == 0:
            raise ValueError("OpenAI no generó reglas. Respuesta vacía.")
        
        print("[INFO] Reglas generadas exitosamente")
        
        return rules
    
    except Exception as e:
        raise RuntimeError(f"Error al generar reglas con OpenAI: {e}")


def save_rules(rules: str, rules_path: str) -> None:
    """
    Guarda las reglas generadas en el archivo especificado.
    
    Args:
        rules: Contenido de las reglas
        rules_path: Ruta donde guardar las reglas
    """
    # Crear directorio si no existe
    rules_dir = os.path.dirname(rules_path)
    if rules_dir and not os.path.exists(rules_dir):
        print(f"[INFO] Creando directorio {rules_dir}...")
        os.makedirs(rules_dir, exist_ok=True)
    
    # Guardar reglas
    with open(rules_path, 'w', encoding='utf-8') as f:
        f.write(f"# Reglas generadas automáticamente por generate_suricata_rules.py\n")
        f.write(f"# Fecha: {subprocess.check_output(['date'], text=True).strip()}\n\n")
        f.write(rules)
    
    print(f"[INFO] Reglas guardadas en {rules_path}")


def reload_suricata() -> bool:
    """
    Recarga las reglas en Suricata usando suricatactl.
    
    Returns:
        True si se recargó exitosamente, False en caso contrario
    """
    print("[INFO] Recargando reglas en Suricata...")
    
    try:
        # Intentar recargar con suricatactl
        result = subprocess.run(
            ['suricatactl', 'reload-rules'],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("[INFO] Reglas recargadas exitosamente en Suricata")
        print(f"[OUTPUT] {result.stdout}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error al recargar reglas: {e.stderr}")
        return False
    
    except FileNotFoundError:
        print("[WARNING] suricatactl no encontrado. Recarga manualmente con:")
        print("  sudo suricatactl reload-rules")
        return False


def print_summary(rules: str, rules_path: str) -> None:
    """
    Imprime un resumen de las reglas generadas.
    
    Args:
        rules: Contenido de las reglas
        rules_path: Ruta donde se guardaron las reglas
    """
    print("\n" + "=" * 60)
    print("RESUMEN DE REGLAS GENERADAS")
    print("=" * 60)
    
    # Contar reglas (líneas que empiezan con "alert")
    rule_count = sum(1 for line in rules.split('\n') if line.strip().startswith('alert'))
    comment_count = sum(1 for line in rules.split('\n') if line.strip().startswith('#'))
    
    print(f"Ubicación: {rules_path}")
    print(f"Reglas generadas: {rule_count}")
    print(f"Comentarios: {comment_count}")
    print(f"Tamaño: {len(rules)} caracteres")
    
    print("\n[VISTA PREVIA]")
    print("-" * 60)
    # Mostrar primeras 20 líneas
    preview_lines = rules.split('\n')[:20]
    for line in preview_lines:
        print(line)
    
    if len(rules.split('\n')) > 20:
        remaining_lines = len(rules.split('\n')) - 20
        print(f"... ({remaining_lines} líneas más)")
    
    print("=" * 60)


def validate_args(args: argparse.Namespace) -> None:
    """
    Valida los argumentos proporcionados.
    
    Args:
        args: Argumentos parseados
    """
    # Verificar que se proporcionó al menos un criterio de filtro
    if not args.ip and args.port is None and not args.flow:
        raise ValueError("Debes proporcionar al menos un criterio de filtro: --ip, --port o --flow")
    
    # Verificar que el archivo de entrada existe
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"El archivo de entrada {args.input} no existe.")
    
    # Verificar API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("La variable de entorno OPENAI_API_KEY no está configurada.")
    
    # Verificar permisos para escribir reglas si se usa --apply
    if args.apply:
        rules_dir = os.path.dirname(args.rules_path)
        if rules_dir and not os.path.exists(rules_dir):
            # Verificar si podemos crear el directorio
            try:
                os.makedirs(rules_dir, exist_ok=True)
            except PermissionError:
                raise PermissionError(
                    f"No tienes permisos para crear {rules_dir}. "
                    "Ejecuta el script con sudo o cambia --rules-path."
                )


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description='Genera reglas de Suricata automáticamente usando OpenAI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python generate_suricata_rules.py --ip 192.168.1.50 --input /var/log/suricata/eve.json --apply
  python generate_suricata_rules.py --port 3333 --input eve.json --output sospechoso.json
  python generate_suricata_rules.py --flow 12345 --input eve.json --apply
        """
    )
    
    # Argumentos de filtro
    parser.add_argument('--ip', type=str, help='IP a filtrar (src_ip o dest_ip)')
    parser.add_argument('--port', type=int, help='Puerto a filtrar (src_port o dest_port)')
    parser.add_argument('--flow', type=str, help='Flow ID a filtrar')
    
    # Argumentos de archivos
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Ruta al archivo eve.json de Suricata'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='sospechoso.json',
        help='Ruta donde guardar el JSON filtrado (default: sospechoso.json)'
    )
    parser.add_argument(
        '--rules-path',
        type=str,
        default=DEFAULT_RULES_PATH,
        help=f'Ruta donde guardar las reglas generadas (default: {DEFAULT_RULES_PATH})'
    )
    
    # Opciones
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Guardar reglas y recargar Suricata automáticamente'
    )
    
    args = parser.parse_args()
    
    try:
        # Validar argumentos
        print("[INFO] Validando argumentos...")
        validate_args(args)
        
        # Obtener API key
        api_key = os.getenv('OPENAI_API_KEY')
        
        # 1. Filtrar eventos
        print("\n[PASO 1/5] Filtrando eventos...")
        event_count = filter_events(
            args.input,
            args.output,
            ip=args.ip,
            port=args.port,
            flow_id=args.flow
        )
        
        if event_count == 0:
            print("[WARNING] No se encontraron eventos que coincidan con los filtros.")
            print("[INFO] El script continuará, pero OpenAI puede no generar reglas útiles.")
        
        # 2. Subir archivo a OpenAI
        print("\n[PASO 2/5] Subiendo archivo a OpenAI...")
        file_id = upload_to_openai(args.output, api_key)
        
        # 3. Generar reglas
        print("\n[PASO 3/5] Generando reglas con OpenAI...")
        rules = generate_rules(file_id, api_key, args.output)
        
        # 4. Guardar reglas
        print("\n[PASO 4/5] Guardando reglas...")
        if args.apply:
            save_rules(rules, args.rules_path)
        else:
            # Si no se usa --apply, guardar en archivo temporal para mostrar
            temp_path = "generated_rules_preview.rules"
            save_rules(rules, temp_path)
            print(f"[INFO] Reglas guardadas en {temp_path} (preview)")
            print("[INFO] Usa --apply para guardar en la ubicación final y recargar Suricata")
        
        # 5. Recargar Suricata (si se usa --apply)
        if args.apply:
            print("\n[PASO 5/5] Recargando Suricata...")
            reload_suricata()
        
        # Resumen
        rules_path = args.rules_path if args.apply else "generated_rules_preview.rules"
        print_summary(rules, rules_path)
        
        print("\n[INFO] Proceso completado exitosamente!")
        
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

