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
            print(f"      ⚠️  WARNING: El archivo {self.eve_json_path} no existe.")
            return []
        
        filtered_events = []
        
        try:
            # Leer archivo JSON (puede ser JSONL - una línea por evento)
            with open(self.eve_json_path, 'r', encoding='utf-8') as f:
                # Intentar leer como JSON array primero
                try:
                    events = json.load(f)
                    if not isinstance(events, list):
                        events = [events]
                    print(f"      📄 Formato: JSON array ({len(events)} eventos)")
                except json.JSONDecodeError:
                    # Si falla, intentar como JSONL (una línea por evento)
                    f.seek(0)
                    events = []
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line:
                            try:
                                events.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                    print(f"      📄 Formato: JSONL (JSON Lines) - {len(events)} eventos leídos")
            
            print(f"      📊 Total de eventos en archivo: {len(events)}")
            print(f"      🔍 Filtrando por tipos: {', '.join(event_types)}")
            
            # Filtrar eventos por tipo
            event_type_counts = {}
            for event in events:
                event_type = event.get('event_type', 'unknown')
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
                if event_type in event_types:
                    filtered_events.append(event)
            
            print(f"      📈 Distribución de eventos:")
            for ev_type, count in sorted(event_type_counts.items()):
                marker = "✅" if ev_type in event_types else "  "
                print(f"         {marker} {ev_type}: {count}")
            
            print(f"      ✅ Eventos filtrados: {len(filtered_events)} de {len(events)} totales")
            
        except Exception as e:
            print(f"      ❌ ERROR al leer/filtrar eventos: {e}")
            import traceback
            print(f"      📋 Traceback: {traceback.format_exc()}")
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
        print(f"[ALERTA] ⚠️  MINERÍA SOSPECHOSA DETECTADA POR ML (#{self.detection_count})")
        print(f"[INFO] Timestamp: {self.last_detection_time.isoformat()}")
        print(f"{'='*60}")
        
        # PASO CRÍTICO: Verificar si Suricata ya detectó esta amenaza
        print(f"\n[3.1] 🔍 Verificando si Suricata ya tiene alertas para esta amenaza...")
        print(f"      Buscando alertas en los últimos 120 segundos...")
        suricata_has_alert = self.check_suricata_alerts(time_window_seconds=120)
        
        if suricata_has_alert:
            print(f"      ✅ RESULTADO: Suricata YA tiene alertas activas")
            print(f"      📋 Acción: No se generarán reglas nuevas (Suricata ya está cubriendo)")
            print(f"      ℹ️  El modelo ML complementó la detección, pero Suricata ya la detectó")
            return
        
        print(f"      ⚠️  RESULTADO: Suricata NO tiene alertas para esta amenaza")
        print(f"      📋 Acción: Proceder a generar reglas automáticas...")
        
        # Leer y filtrar eventos de Suricata
        print(f"\n[3.2] 📂 Leyendo eventos de eve.json...")
        print(f"      Ruta: {self.eve_json_path}")
        
        if not os.path.exists(self.eve_json_path):
            print(f"      ❌ ERROR: El archivo eve.json no existe")
            print(f"      📋 Acción: Los eventos del ingest se escribirán automáticamente aquí")
            print(f"      💡 Sugerencia: Envía eventos por /ingest/eve primero")
            return
        
        events = self.filter_suricata_events(['alert', 'dns', 'http', 'tls', 'flow'])
        
        if not events:
            print(f"      ⚠️  WARNING: No se encontraron eventos relevantes en eve.json")
            print(f"      📋 Acción: No se pueden generar reglas sin contexto de tráfico")
            print(f"      💡 Sugerencia: Envía eventos por /ingest/eve para generar contexto")
            return
        
        print(f"      ✅ Eventos encontrados: {len(events)} eventos relevantes")
        print(f"      📊 Tipos de eventos: {', '.join(set(e.get('event_type', 'unknown') for e in events))}")
        
        # Generar reglas con OpenAI
        print(f"\n[3.3] 🤖 Generando reglas con OpenAI...")
        print(f"      Modelo: {OPENAI_MODEL}")
        print(f"      Enviando {len(events)} eventos para análisis...")
        
        rules = self.generate_rules_with_openai(events)
        
        if not rules:
            print(f"      ❌ ERROR: No se pudieron generar reglas")
            print(f"      💡 Verifica que OPENAI_API_KEY esté configurada")
            return
        
        rule_lines = len([l for l in rules.split('\n') if l.strip() and not l.strip().startswith('#')])
        print(f"      ✅ Reglas generadas: {rule_lines} reglas")
        
        # Parsear reglas
        print(f"\n[3.4] 📝 Parseando reglas...")
        parsed_rules = self.parse_suricata_rules(rules)
        print(f"      ✅ Reglas parseadas: {len(parsed_rules)} reglas listas para enviar")
        for i, rule in enumerate(parsed_rules[:3], 1):  # Mostrar primeras 3
            print(f"         {i}. {rule.get('name', 'Sin nombre')} (SID: {rule.get('sid', 'N/A')})")
        if len(parsed_rules) > 3:
            print(f"         ... y {len(parsed_rules) - 3} más")
        
        # Guardar en archivo (backup)
        print(f"\n[3.5] 💾 Guardando reglas en archivo (backup)...")
        self.save_rules_to_file(rules)
        print(f"      ✅ Reglas guardadas en: {self.rules_file}")
        
        # Enviar al backend
        print(f"\n[3.6] 📤 Enviando reglas al backend...")
        print(f"      URL: {self.backend_url}/rulesets/rules")
        success_count = self.send_rules_to_backend(parsed_rules)
        
        if success_count > 0:
            print(f"\n{'='*60}")
            print(f"[SUCCESS] ✅ {success_count}/{len(parsed_rules)} reglas enviadas exitosamente")
            print(f"[INFO] 📊 Las reglas deberían aparecer en el Dashboard:")
            print(f"      http://localhost:8080/rules")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f"[ERROR] ❌ No se pudieron enviar reglas al backend")
            print(f"      💡 Verifica que el backend esté corriendo en {self.backend_url}")
            print(f"{'='*60}")
    
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
            cycle_count = 0
            while True:
                cycle_count += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"\n{'='*60}")
                print(f"[CICLO #{cycle_count}] {timestamp}")
                print(f"{'='*60}")
                
                # 1. Recolectar métricas
                print("[PASO 1/5] 📊 Recolectando métricas del sistema...")
                metrics = self.collect_system_metrics()
                print(f"  ✅ Métricas recolectadas:")
                print(f"     - CPU: {metrics['cpu_percent']:.2f}%")
                print(f"     - RAM: {metrics['ram_percent']:.2f}%")
                print(f"     - Red enviado: {metrics['bytes_sent']:,} bytes")
                print(f"     - Red recibido: {metrics['bytes_recv']:,} bytes")
                print(f"     - Procesos: {metrics['process_count']}")
                print(f"     - XMRig detectado: {'Sí' if metrics['xmrig_detected'] else 'No'}")
                
                # 2. Clasificar estado
                print(f"[PASO 2/5] 🤖 Clasificando con modelo ML...")
                result = self.classify_state(metrics)
                print(f"  ✅ Clasificación completada:")
                print(f"     - Estado predicho: {result['state'].upper()}")
                print(f"     - Probabilidad: {result['probability']:.4f} ({result['probability']*100:.2f}%)")
                print(f"     - Clase: {result['prediction']} ({'Minería' if result['prediction'] == 1 else 'Normal'})")
                
                # 3. Verificar si hay detección
                if result['state'] == "mineria_sospechosa":
                    print(f"[PASO 3/5] ⚠️  MINERÍA SOSPECHOSA DETECTADA")
                    print(f"  🔍 Iniciando proceso de generación de reglas...")
                    self.handle_mining_detection()
                else:
                    print(f"[PASO 3/5] ✅ Estado normal - No se requiere acción")
                
                # 4. Resumen del ciclo
                print(f"[PASO 4/5] 📝 Resumen del ciclo:")
                print(f"     - Total detecciones hasta ahora: {self.detection_count}")
                if self.last_detection_time:
                    print(f"     - Última detección: {self.last_detection_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 5. Esperar intervalo
                print(f"[PASO 5/5] ⏳ Esperando {self.interval} segundos hasta el próximo ciclo...")
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

