#!/usr/bin/env python3
"""
Pipeline automatizado de detección de cryptojacking.
Integra recolección de métricas, detección ML y generación de reglas Suricata.
"""

import time
import os
import sys
import json
import argparse
import re
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any

import psutil  # type: ignore

try:
    from openai import OpenAI  # type: ignore
except ImportError:
    print("[ERROR] La biblioteca 'openai' no está instalada.")
    print("[INFO] Instálala con: pip install openai")
    sys.exit(1)

# Importar el detector de cryptojacking
try:
    from detect import CryptojackingDetector
except ImportError:
    print("[ERROR] No se puede importar CryptojackingDetector de detect.py")
    print("[INFO] Asegúrate de que detect.py esté en el mismo directorio")
    sys.exit(1)

# Configuración
DEFAULT_EVE_JSON = "/var/log/suricata/eve.json"
DEFAULT_RULES_FILE = "rules/custom_rules.rules"
DEFAULT_BACKEND_URL = "http://localhost:8080"
OPENAI_MODEL = "gpt-4o-mini"
INTERVAL_SECONDS = 10  # Intervalo de monitoreo en segundos

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


class PipelineMonitor:
    """Monitor principal que integra recolección, detección y generación de reglas."""
    
    def __init__(
        self,
        eve_json_path: str = DEFAULT_EVE_JSON,
        rules_file: str = DEFAULT_RULES_FILE,
        interval: int = INTERVAL_SECONDS,
        backend_url: str = DEFAULT_BACKEND_URL
    ):
        """
        Inicializa el monitor del pipeline.
        
        Args:
            eve_json_path: Ruta al archivo eve.json de Suricata
            rules_file: Archivo donde guardar las reglas generadas
            interval: Intervalo de monitoreo en segundos
            backend_url: URL base del backend (ej: http://localhost:8080)
        """
        self.eve_json_path = eve_json_path
        self.rules_file = rules_file
        self.interval = interval
        self.backend_url = backend_url.rstrip('/')
        
        # Inicializar detector de cryptojacking
        try:
            self.detector = CryptojackingDetector()
            print("[INFO] Detector de cryptojacking inicializado")
        except Exception as e:
            print(f"[ERROR] Error al inicializar detector: {e}")
            sys.exit(1)
        
        # Verificar API key de OpenAI
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("[WARNING] OPENAI_API_KEY no está configurada.")
            print("[WARNING] La generación de reglas no funcionará sin la API key.")
        
        # Contador de detecciones
        self.detection_count = 0
        self.last_detection_time = None
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """
        Recolecta métricas del sistema usando el detector.
        
        Returns:
            Diccionario con las métricas recolectadas
        """
        return self.detector.collect_metrics()
    
    def classify_state(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clasifica el estado del sistema usando el modelo ML.
        
        Args:
            metrics: Métricas del sistema
        
        Returns:
            Resultado de la clasificación con prediction, probability, class
        """
        result = self.detector.predict(metrics)
        
        # Mapear a estados más descriptivos
        if result['prediction'] == 1:
            state = "mineria_sospechosa"
        elif result['probability'] < 0.3:
            state = "normal"
        else:
            state = "actividad_legitima"
        
        result['state'] = state
        return result
    
    def filter_suricata_events(self, event_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Lee y filtra eventos relevantes del archivo eve.json de Suricata.
        
        Args:
            event_types: Tipos de eventos a filtrar (default: ['alert', 'dns', 'http', 'tls'])
        
        Returns:
            Lista de eventos filtrados
        """
        if event_types is None:
            event_types = ['alert', 'dns', 'http', 'tls', 'flow']
        
        if not os.path.exists(self.eve_json_path):
            print(f"[WARNING] El archivo {self.eve_json_path} no existe.")
            return []
        
        print(f"[INFO] Leyendo eventos de {self.eve_json_path}...")
        
        filtered_events = []
        
        try:
            # Leer archivo JSON (puede ser JSONL - una línea por evento)
            with open(self.eve_json_path, 'r', encoding='utf-8') as f:
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
            
            # Filtrar eventos por tipo
            for event in events:
                event_type = event.get('event_type') or event.get('event_type')
                if event_type in event_types:
                    filtered_events.append(event)
            
            print(f"[INFO] Eventos filtrados: {len(filtered_events)} de {len(events)} totales")
            
        except Exception as e:
            print(f"[ERROR] Error al leer/filtrar eventos: {e}")
            return []
        
        return filtered_events
    
    def check_suricata_alerts(self, time_window_seconds: int = 60) -> bool:
        """
        Verifica si Suricata ya ha levantado alertas recientes.
        
        Args:
            time_window_seconds: Ventana de tiempo en segundos para buscar alertas recientes
        
        Returns:
            True si Suricata ya tiene alertas, False si no
        """
        if not os.path.exists(self.eve_json_path):
            return False
        
        try:
            # Leer eventos recientes
            current_time = datetime.now().timestamp()
            time_threshold = current_time - time_window_seconds
            
            with open(self.eve_json_path, 'r', encoding='utf-8') as f:
                # Leer como JSONL
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        event = json.loads(line)
                        
                        # Verificar si es una alerta de Suricata
                        if event.get('event_type') == 'alert':
                            # Verificar timestamp (puede estar en diferentes formatos)
                            event_time = None
                            if 'timestamp' in event:
                                try:
                                    # Intentar parsear timestamp
                                    if isinstance(event['timestamp'], str):
                                        # Intentar parsear ISO format
                                        try:
                                            event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')).timestamp()
                                        except:
                                            # Si falla, usar timestamp actual como aproximación
                                            event_time = current_time
                                    else:
                                        event_time = float(event['timestamp'])
                                except:
                                    pass
                            
                            # Si la alerta es reciente, Suricata ya detectó algo
                            if event_time and event_time >= time_threshold:
                                # Verificar si la alerta es relacionada con cryptojacking/mining
                                alert_data = event.get('alert', {})
                                signature = alert_data.get('signature', '')
                                category = alert_data.get('category', '')
                                msg = alert_data.get('signature', '')
                                
                                # Palabras clave relacionadas con cryptojacking
                                crypto_keywords = ['mining', 'crypto', 'monero', 'xmr', 'stratum', 
                                                  'pool', 'minexmr', 'supportxmr', 'hashvault']
                                
                                alert_text = f"{signature} {category} {msg}".lower()
                                if any(keyword in alert_text for keyword in crypto_keywords):
                                    return True
                    
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            return False
        
        except Exception as e:
            print(f"[WARNING] Error al verificar alertas de Suricata: {e}")
            # En caso de error, asumimos que no hay alertas para no bloquear el proceso
            return False
    
    def generate_rules_with_openai(self, events: List[Dict[str, Any]]) -> Optional[str]:
        """
        Genera reglas de Suricata usando OpenAI basándose en los eventos.
        
        Args:
            events: Lista de eventos de Suricata
        
        Returns:
            Reglas generadas o None si hay error
        """
        if not self.api_key:
            print("[ERROR] OPENAI_API_KEY no está configurada.")
            return None
        
        if not events:
            print("[WARNING] No hay eventos para analizar.")
            return None
        
        # Crear archivo temporal con eventos filtrados
        temp_file = "temp_suricata_events.json"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            
            client = OpenAI(api_key=self.api_key)
            
            print("[INFO] Generando reglas con OpenAI...")
            
            # Leer contenido del archivo
            with open(temp_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Limitar el tamaño si es muy grande
            if len(file_content) > 10000:
                file_content = file_content[:10000] + "\n... (contenido truncado)"
            
            # Crear prompt completo
            full_prompt = f"""{PROMPT_TEMPLATE}

Contenido del archivo JSON a analizar:
```json
{file_content}
```
"""
            
            # Generar reglas con OpenAI
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
                print("[WARNING] OpenAI no generó reglas. Respuesta vacía.")
                return None
            
            print("[INFO] Reglas generadas exitosamente")
            
            # Limpiar archivo temporal
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return rules
        
        except Exception as e:
            print(f"[ERROR] Error al generar reglas con OpenAI: {e}")
            # Limpiar archivo temporal en caso de error
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return None
    
    def parse_suricata_rules(self, rules_text: str) -> List[Dict[str, Any]]:
        """
        Parsea las reglas de Suricata generadas por OpenAI.
        Extrae SID, mensaje, contenido y otros campos.
        
        Args:
            rules_text: Texto con las reglas de Suricata
        
        Returns:
            Lista de diccionarios con las reglas parseadas
        """
        parsed_rules = []
        lines = rules_text.split('\n')
        
        current_comment = ""
        for line in lines:
            line = line.strip()
            
            # Ignorar líneas vacías
            if not line:
                continue
            
            # Capturar comentarios
            if line.startswith('#'):
                current_comment = line.lstrip('#').strip()
                continue
            
            # Buscar reglas alert (formato: alert protocol src_ip src_port -> dst_ip dst_port (msg:"..."; content:"..."; sid:...; rev:...;))
            if line.startswith('alert '):
                rule_dict = {
                    'vendor': 'suricata',
                    'sid': None,
                    'name': '',
                    'body': line,
                    'tags': ['auto-generated', 'cryptojacking'],
                    'enabled': True
                }
                
                # Extraer SID
                sid_match = re.search(r'sid:\s*(\d+)', line)
                if sid_match:
                    rule_dict['sid'] = int(sid_match.group(1))
                
                # Extraer mensaje para el nombre
                msg_match = re.search(r'msg:\s*"([^"]+)"', line)
                if msg_match:
                    rule_dict['name'] = msg_match.group(1)
                elif current_comment:
                    rule_dict['name'] = current_comment[:100]  # Limitar longitud
                else:
                    rule_dict['name'] = f"Auto-generated rule #{self.detection_count}"
                
                # Si no hay SID, generar uno basado en timestamp
                if rule_dict['sid'] is None:
                    rule_dict['sid'] = 2000000 + self.detection_count * 100 + len(parsed_rules)
                
                parsed_rules.append(rule_dict)
                current_comment = ""  # Reset comentario después de usar
        
        return parsed_rules
    
    def send_rules_to_backend(self, parsed_rules: List[Dict[str, Any]]) -> int:
        """
        Envía las reglas parseadas al backend mediante API REST.
        
        Args:
            parsed_rules: Lista de reglas parseadas
        
        Returns:
            Número de reglas enviadas exitosamente
        """
        if not parsed_rules:
            return 0
        
        api_url = f"{self.backend_url}/rulesets/rules"
        success_count = 0
        
        print(f"[INFO] Enviando {len(parsed_rules)} reglas al backend ({api_url})...")
        
        for rule in parsed_rules:
            try:
                response = requests.post(
                    api_url,
                    json=rule,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    success_count += 1
                    print(f"  ✓ Regla enviada: {rule['name']} (SID: {rule['sid']})")
                else:
                    print(f"  ✗ Error al enviar regla '{rule['name']}': {response.status_code} - {response.text}")
            
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Error de conexión al enviar regla '{rule['name']}': {e}")
                continue
        
        print(f"[INFO] {success_count}/{len(parsed_rules)} reglas enviadas exitosamente al backend")
        return success_count
    
    def save_rules_to_file(self, rules: str) -> None:
        """
        Guarda las reglas generadas en el archivo (backup).
        
        Args:
            rules: Contenido de las reglas
        """
        rules_dir = os.path.dirname(self.rules_file)
        if rules_dir and not os.path.exists(rules_dir):
            os.makedirs(rules_dir, exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        with open(self.rules_file, 'a', encoding='utf-8') as f:
            f.write(f"\n# Reglas generadas automáticamente - {timestamp}\n")
            f.write(f"# Detección #{self.detection_count}\n\n")
            f.write(rules)
            f.write("\n\n")
        
        print(f"[INFO] Reglas guardadas en {self.rules_file} (backup)")
    
    def handle_mining_detection(self) -> None:
        """
        Maneja la detección de minería sospechosa SOLO si Suricata no la detectó.
        Optimiza el trabajo de Suricata creando reglas automáticas cuando Suricata
        no detecta una amenaza que el modelo ML sí detecta.
        
        Flujo:
        1. Verifica si Suricata ya tiene alertas para esta amenaza
        2. Si Suricata NO detectó, entonces:
           - Lee eve.json
           - Filtra eventos relevantes
           - Envía a OpenAI
           - Genera reglas
           - Envía al backend
        3. Si Suricata SÍ detectó, no hace nada (ya está cubierto)
        """
        self.detection_count += 1
        self.last_detection_time = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"[ALERTA] ⚠️  Minería sospechosa detectada por ML (#{self.detection_count})")
        print(f"[INFO] Timestamp: {self.last_detection_time.isoformat()}")
        print(f"{'='*60}")
        
        # PASO CRÍTICO: Verificar si Suricata ya detectó esta amenaza
        print(f"\n[VERIFICACIÓN] Comprobando si Suricata ya tiene alertas para esta amenaza...")
        suricata_has_alert = self.check_suricata_alerts(time_window_seconds=120)
        
        if suricata_has_alert:
            print(f"[INFO] ✅ Suricata ya tiene alertas activas para esta amenaza")
            print(f"[INFO] No es necesario crear reglas nuevas (Suricata ya está cubriendo)")
            print(f"[INFO] El modelo ML complementó la detección, pero Suricata ya la detectó")
            return
        
        print(f"[INFO] ⚠️  Suricata NO tiene alertas para esta amenaza")
        print(f"[INFO] Generando reglas automáticas para optimizar detección de Suricata...")
        print(f"{'='*60}")
        
        # 1. Filtrar eventos de Suricata
        print(f"\n[PASO 1/5] Leyendo y filtrando eventos de {self.eve_json_path}...")
        events = self.filter_suricata_events()
        
        if not events:
            print("[WARNING] No se encontraron eventos relevantes en eve.json")
            print("[INFO] El pipeline continuará, pero puede que no haya datos suficientes")
            events = []
        
        # 2. Generar reglas con OpenAI
        print(f"\n[PASO 2/5] Enviando {len(events)} eventos a OpenAI para análisis...")
        rules = self.generate_rules_with_openai(events)
        
        if not rules:
            print("[ERROR] No se pudieron generar reglas con OpenAI")
            print("[INFO] Verifica que OPENAI_API_KEY esté configurada correctamente")
            return
        
        # 3. Guardar reglas en archivo (backup)
        print(f"\n[PASO 3/5] Guardando reglas en archivo de respaldo...")
        self.save_rules_to_file(rules)
        
        # 4. Parsear reglas
        print(f"\n[PASO 4/5] Parseando reglas generadas...")
        parsed_rules = self.parse_suricata_rules(rules)
        
        if not parsed_rules:
            print("[WARNING] No se pudieron parsear reglas para enviar al backend")
            return
        
        # 5. Enviar reglas al backend (aparecerán en Dashboard)
        print(f"\n[PASO 5/5] Enviando {len(parsed_rules)} reglas al backend...")
        success_count = self.send_rules_to_backend(parsed_rules)
        
        print(f"\n{'='*60}")
        print(f"[INFO] ✅ Pipeline completado exitosamente!")
        print(f"[INFO] Reglas enviadas al backend: {success_count}/{len(parsed_rules)}")
        print(f"[INFO] Las reglas ahora están disponibles en el Dashboard")
        print(f"[INFO] Estas reglas ayudarán a Suricata a detectar amenazas similares en el futuro")
        print(f"{'='*60}\n")
    
    def run(self) -> None:
        """Ejecuta el pipeline de monitoreo continuo."""
        print("=" * 60)
        print("PIPELINE DE MONITOREO DE CRYPTOJACKING")
        print("=" * 60)
        print(f"[INFO] Intervalo de monitoreo: {self.interval} segundos")
        print(f"[INFO] Archivo eve.json: {self.eve_json_path}")
        print(f"[INFO] Archivo de reglas: {self.rules_file}")
        print("[INFO] Presiona Ctrl+C para detener")
        print("=" * 60)
        
        try:
            while True:
                # 1. Recolectar métricas
                metrics = self.collect_system_metrics()
                
                # 2. Clasificar estado
                result = self.classify_state(metrics)
                
                # 3. Mostrar resultado
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{timestamp}] Estado: {result['state'].upper()}")
                print(f"  Probabilidad: {result['probability']:.4f} ({result['probability']*100:.2f}%)")
                print(f"  CPU: {metrics['cpu_percent']:.2f}% | RAM: {metrics['ram_percent']:.2f}%")
                
                # 4. Si detecta minería sospechosa, generar reglas
                if result['state'] == "mineria_sospechosa":
                    self.handle_mining_detection()
                
                # 5. Esperar intervalo
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            print("\n\n[INFO] Pipeline detenido por el usuario")
            print(f"[INFO] Total de detecciones: {self.detection_count}")
            if self.last_detection_time:
                print(f"[INFO] Última detección: {self.last_detection_time}")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Pipeline automatizado de detección de cryptojacking',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--eve-json',
        type=str,
        default=DEFAULT_EVE_JSON,
        help=f'Ruta al archivo eve.json de Suricata (default: {DEFAULT_EVE_JSON})'
    )
    
    parser.add_argument(
        '--rules-file',
        type=str,
        default=DEFAULT_RULES_FILE,
        help=f'Archivo donde guardar las reglas (default: {DEFAULT_RULES_FILE})'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=INTERVAL_SECONDS,
        help=f'Intervalo de monitoreo en segundos (default: {INTERVAL_SECONDS})'
    )
    
    parser.add_argument(
        '--backend-url',
        type=str,
        default=DEFAULT_BACKEND_URL,
        help=f'URL base del backend (default: {DEFAULT_BACKEND_URL})'
    )
    
    args = parser.parse_args()
    
    # Crear y ejecutar monitor
    monitor = PipelineMonitor(
        eve_json_path=args.eve_json,
        rules_file=args.rules_file,
        interval=args.interval,
        backend_url=args.backend_url
    )
    
    monitor.run()


if __name__ == "__main__":
    main()

