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
import subprocess
import signal
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import psutil  # type: ignore

# Importar el detector de cryptojacking
try:
    from detect import CryptojackingDetector
except ImportError:
    print("[ERROR] No se puede importar CryptojackingDetector de detect.py")
    print("[INFO] Asegúrate de que detect.py esté en el mismo directorio")
    sys.exit(1)

# Importar el analizador de eventos EVE
try:
    from eve_analyzer import EVEAnalyzer
except ImportError:
    print("[ERROR] No se puede importar EVEAnalyzer de eve_analyzer.py")
    print("[INFO] Asegúrate de que eve_analyzer.py esté en el mismo directorio")
    sys.exit(1)

# Configuración
DEFAULT_EVE_JSON = "/var/log/suricata/eve.json"
DEFAULT_RULES_FILE = "rules/custom_rules.rules"
DEFAULT_SURICATA_RULES_FILE = "/var/log/suricata/rules/generated.rules"
DEFAULT_BACKEND_URL = "http://localhost:8080"
INTERVAL_SECONDS = 10  # Intervalo de monitoreo en segundos


class PipelineMonitor:
    """Monitor principal que integra recolección, detección y generación de reglas."""
    
    def __init__(
        self,
        eve_json_path: str = DEFAULT_EVE_JSON,
        rules_file: str = DEFAULT_RULES_FILE,
        suricata_rules_file: str = DEFAULT_SURICATA_RULES_FILE,
        interval: int = INTERVAL_SECONDS,
        backend_url: str = DEFAULT_BACKEND_URL
    ):
        """
        Inicializa el monitor del pipeline.
        
        Args:
            eve_json_path: Ruta al archivo eve.json de Suricata
            rules_file: Archivo donde guardar las reglas generadas (backup)
            suricata_rules_file: Archivo de reglas de Suricata donde se escribirán las reglas
            interval: Intervalo de monitoreo en segundos
            backend_url: URL base del backend (ej: http://localhost:8080)
        """
        self.eve_json_path = eve_json_path
        self.rules_file = rules_file
        # Usar variable de entorno si está disponible, sino usar el parámetro
        self.suricata_rules_file = os.getenv('SURICATA_RULES_FILE', suricata_rules_file)
        self.interval = interval
        self.backend_url = backend_url.rstrip('/')
        
        # Inicializar detector de cryptojacking
        try:
            self.detector = CryptojackingDetector()
            print("[INFO] Detector de cryptojacking inicializado")
        except Exception as e:
            print(f"[ERROR] Error al inicializar detector: {e}")
            sys.exit(1)
        
        # Inicializar analizador de eventos EVE
        self.eve_analyzer = EVEAnalyzer(base_sid=2000000)
        
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
    
    def _read_all_recent_events(self, max_events: int = 100, time_window_minutes: int = 10) -> List[Dict[str, Any]]:
        """
        Lee TODOS los eventos recientes de eve.json sin filtrar por tipo.
        Cuando el modelo detecta una amenaza, el analizador debe examinar todo el contexto.
        
        Args:
            max_events: Número máximo de eventos a leer (los más recientes)
            time_window_minutes: Ventana de tiempo en minutos para considerar eventos recientes
        
        Returns:
            Lista de eventos recientes (sin filtrar por tipo)
        """
        if not os.path.exists(self.eve_json_path):
            return []
        
        events = []
        current_time = datetime.now()
        time_threshold = current_time - timedelta(minutes=time_window_minutes)
        
        try:
            # Leer archivo JSONL (una línea por evento)
            with open(self.eve_json_path, 'r', encoding='utf-8') as f:
                all_lines = []
                for line in f:
                    line = line.strip()
                    if line:
                        all_lines.append(line)
                
                # Leer desde el final (eventos más recientes primero)
                for line in reversed(all_lines[-max_events:]):
                    try:
                        event = json.loads(line)
                        
                        # Intentar filtrar por timestamp si está disponible
                        event_time = None
                        if 'timestamp' in event:
                            try:
                                if isinstance(event['timestamp'], str):
                                    event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                                else:
                                    event_time = datetime.fromtimestamp(event['timestamp'])
                            except:
                                pass
                        
                        # Si no hay timestamp o está dentro de la ventana de tiempo, incluir el evento
                        if event_time is None or event_time >= time_threshold:
                            events.append(event)
                            
                    except json.JSONDecodeError:
                        continue
            
            # Invertir para tener eventos en orden cronológico
            events.reverse()
            
            print(f"      ✅ Eventos leídos: {len(events)} eventos recientes (sin filtrar por tipo)")
            if events:
                event_types = {}
                for event in events:
                    ev_type = event.get('event_type', 'unknown')
                    event_types[ev_type] = event_types.get(ev_type, 0) + 1
                print(f"      📊 Tipos de eventos encontrados: {', '.join(f'{k}({v})' for k, v in sorted(event_types.items()))}")
            
        except Exception as e:
            print(f"      ❌ ERROR al leer eventos: {e}")
            import traceback
            print(f"      📋 Traceback: {traceback.format_exc()}")
            return []
        
        return events
    
    def _generate_synthetic_events_from_metrics(self) -> List[Dict[str, Any]]:
        """
        Genera eventos sintéticos basados en las métricas del sistema detectadas.
        Útil cuando no hay eventos en eve.json pero el modelo detectó minería.
        
        Returns:
            Lista de eventos sintéticos
        """
        # Obtener métricas recientes
        metrics = self.collect_system_metrics()
        
        # Generar eventos que reflejen la actividad sospechosa detectada
        events = []
        current_time = datetime.now().isoformat()
        
        # Evento de flujo sospechoso (alto tráfico)
        if metrics['bytes_sent'] > 10000 or metrics['bytes_recv'] > 10000:
            events.append({
                'timestamp': current_time,
                'event_type': 'flow',
                'src_ip': '192.168.100.10',  # IP de la víctima (del lab)
                'src_port': 54321,
                'dest_ip': '192.168.100.30',  # IP del pool (del lab)
                'dest_port': 8080,
                'proto': 'TCP',
                'flow_id': 999999,
                'app_proto': 'http',
                'flow': {
                    'pkts_toserver': 150,
                    'pkts_toclient': 120,
                    'bytes_toserver': metrics['bytes_sent'],
                    'bytes_toclient': metrics['bytes_recv'],
                    'start': current_time
                }
            })
        
        # Evento HTTP sospechoso (si hay tráfico alto)
        if metrics['bytes_sent'] > 20000:
            events.append({
                'timestamp': current_time,
                'event_type': 'http',
                'src_ip': '192.168.100.10',
                'src_port': 54322,
                'dest_ip': '192.168.100.30',
                'dest_port': 8080,
                'proto': 'TCP',
                'http': {
                    'hostname': 'pool-api.example.com',
                    'url': '/api/v1/submit',
                    'http_user_agent': 'Mozilla/5.0 (compatible; MinerBot/1.0)',
                    'http_method': 'POST',
                    'status': 200,
                    'length': metrics['bytes_sent']
                },
                'tx_id': 1
            })
        
        return events
    
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
    
    def generate_rules_with_analyzer(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Genera reglas de Suricata usando el analizador local de eventos EVE.
        
        Args:
            events: Lista de eventos de Suricata
        
        Returns:
            Lista de reglas generadas en formato para el backend
        """
        if not events:
            print("[WARNING] ⚠️  No hay eventos para analizar.")
            return []
        
        print("[INFO] 🔍 Iniciando análisis local de eventos EVE...")
        print(f"      📝 Eventos a analizar: {len(events)}")
        
        try:
            # Analizar eventos y generar reglas
            rules = self.eve_analyzer.analyze_events(events)
            
            if not rules:
                print("[WARNING] ⚠️  El analizador no generó reglas.")
                return []
            
            print(f"[INFO] ✅ Análisis completado: {len(rules)} reglas generadas")
            
            # Mostrar resumen de reglas generadas
            print(f"      📋 Resumen de reglas:")
            for i, rule in enumerate(rules[:5], 1):  # Mostrar primeras 5
                print(f"         {i}. {rule.get('name', 'Sin nombre')} (SID: {rule.get('sid', 'N/A')})")
            if len(rules) > 5:
                print(f"         ... y {len(rules) - 5} reglas más")
            
            return rules
        
        except Exception as e:
            print(f"[ERROR] ❌ Error al analizar eventos: {e}")
            import traceback
            print(f"      📋 Traceback: {traceback.format_exc()}")
            return []
    
    def parse_suricata_rules(self, rules_text: str) -> List[Dict[str, Any]]:
        """
        Parsea las reglas de Suricata generadas por Groq.
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
    
    def save_rules_to_suricata_file(self, rules: str) -> None:
        """
        Guarda las reglas generadas en el archivo de reglas de Suricata.
        
        Args:
            rules: Contenido de las reglas (texto)
        """
        if not rules or not rules.strip():
            return
        
        # Crear directorio si no existe
        rules_dir = os.path.dirname(self.suricata_rules_file)
        if rules_dir and not os.path.exists(rules_dir):
            try:
                os.makedirs(rules_dir, exist_ok=True)
                print(f"      📁 Directorio creado: {rules_dir}")
            except Exception as e:
                print(f"      ⚠️  WARNING: No se pudo crear directorio {rules_dir}: {e}")
                print(f"      💡 Las reglas se guardarán solo en el backup")
                return
        
        try:
            # Extraer solo las reglas (sin comentarios de encabezado)
            rule_lines = []
            for line in rules.split('\n'):
                line = line.strip()
                # Incluir solo líneas que son reglas (alert, drop, etc.) o comentarios útiles
                if line and (line.startswith('alert') or line.startswith('drop') or 
                            line.startswith('pass') or (line.startswith('#') and 'regla' in line.lower())):
                    rule_lines.append(line)
            
            if not rule_lines:
                print(f"      ⚠️  WARNING: No se encontraron reglas válidas para guardar")
                return
            
            # Agregar las reglas al archivo de Suricata
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.suricata_rules_file, 'a', encoding='utf-8') as f:
                f.write(f"\n# Reglas generadas automáticamente - {timestamp}\n")
                f.write(f"# Detección #{self.detection_count}\n")
                f.write("\n".join(rule_lines))
                f.write("\n\n")
            
            print(f"[INFO] ✅ Reglas agregadas a {self.suricata_rules_file}")
            
            # Recargar reglas en Suricata automáticamente
            self._reload_suricata_rules()
        
        except PermissionError:
            print(f"      ❌ ERROR: Sin permisos para escribir en {self.suricata_rules_file}")
            print(f"      💡 Verifica permisos del archivo/directorio")
        except Exception as e:
            print(f"      ❌ ERROR al guardar reglas en Suricata: {e}")
    
    def _reload_suricata_rules(self) -> None:
        """
        Intenta recargar las reglas en Suricata automáticamente.
        Prueba múltiples métodos para asegurar que funcione.
        """
        print(f"      🔄 Recargando reglas en Suricata...")
        
        # Método 1: Intentar con suricatactl
        try:
            result = subprocess.run(
                ['suricatactl', 'reload-rules'],
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )
            print(f"      ✅ Reglas recargadas exitosamente con suricatactl")
            if result.stdout:
                print(f"      📋 Output: {result.stdout.strip()}")
            return
        except FileNotFoundError:
            print(f"      ⚠️  suricatactl no encontrado, intentando método alternativo...")
        except subprocess.TimeoutExpired:
            print(f"      ⚠️  Timeout al recargar reglas, intentando método alternativo...")
        except subprocess.CalledProcessError as e:
            print(f"      ⚠️  Error con suricatactl: {e.stderr.strip() if e.stderr else 'unknown error'}")
            print(f"      ⚠️  Intentando método alternativo...")
        except Exception as e:
            print(f"      ⚠️  Error inesperado: {e}")
        
        # Método 2: Intentar enviar señal SIGHUP al proceso de Suricata
        try:
            # Buscar proceso de Suricata
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'suricata' in proc.info['name'].lower():
                        pid = proc.info['pid']
                        os.kill(pid, signal.SIGHUP)
                        print(f"      ✅ Señal SIGHUP enviada a Suricata (PID: {pid})")
                        print(f"      ✅ Reglas recargadas exitosamente")
                        return
                except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
                    continue
        except Exception as e:
            print(f"      ⚠️  No se pudo enviar señal SIGHUP: {e}")
        
        # Método 3: Intentar con systemctl si está disponible
        try:
            result = subprocess.run(
                ['systemctl', 'reload', 'suricata'],
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )
            print(f"      ✅ Reglas recargadas exitosamente con systemctl")
            return
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        except Exception:
            pass
        
        # Si todos los métodos fallan, informar al usuario
        print(f"      ⚠️  WARNING: No se pudo recargar Suricata automáticamente")
        print(f"      💡 Las reglas están guardadas pero Suricata necesita recargarlas manualmente")
        print(f"      💡 Opciones:")
        print(f"         1. Ejecutar: suricatactl reload-rules")
        print(f"         2. Reiniciar Suricata: systemctl restart suricata")
        print(f"         3. Enviar señal: kill -HUP <PID_de_Suricata>")
    
    def save_rules_to_file(self, rules: str) -> None:
        """
        Guarda las reglas generadas en el archivo (backup).
        
        Args:
            rules: Contenido de las reglas (texto)
        """
        if not rules or not rules.strip():
            return
        
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
        
        # Crear directorio y archivo si no existen
        eve_dir = os.path.dirname(self.eve_json_path)
        if eve_dir and not os.path.exists(eve_dir):
            print(f"      📁 Creando directorio: {eve_dir}")
            try:
                os.makedirs(eve_dir, exist_ok=True)
                print(f"      ✅ Directorio creado: {eve_dir}")
            except Exception as e:
                print(f"      ❌ ERROR al crear directorio: {e}")
        
        if not os.path.exists(self.eve_json_path):
            print(f"      📄 Creando archivo eve.json vacío...")
            try:
                with open(self.eve_json_path, 'w', encoding='utf-8') as f:
                    pass  # Crear archivo vacío
                print(f"      ✅ Archivo creado: {self.eve_json_path}")
            except Exception as e:
                print(f"      ❌ ERROR al crear archivo: {e}")
                print(f"      💡 Verifica permisos de escritura en {eve_dir}")
        
        # Cuando el modelo detecta una amenaza, enviar TODOS los eventos recientes a Groq
        # No filtrar por tipo - dejar que Groq analice todo el contexto
        print(f"      📋 Leyendo TODOS los eventos recientes de eve.json...")
        print(f"      📂 Archivo: {self.eve_json_path}")
        print(f"      💡 No se aplicarán filtros restrictivos - Groq analizará todo el contexto")
        print(f"      ⏱️  Ventana de tiempo: últimos 10 minutos, máximo 100 eventos")
        
        events = self._read_all_recent_events(max_events=100, time_window_minutes=10)
        
        if not events:
            print(f"      ⚠️  WARNING: No se encontraron eventos en eve.json")
            print(f"      📋 El archivo existe pero está vacío o no tiene eventos recientes")
            print(f"      💡 Sugerencia: Envía eventos por /ingest/eve o ejecuta simular.sh")
            print(f"      📝 Generando eventos sintéticos basados en métricas del sistema...")
            
            # Generar eventos sintéticos basados en las métricas detectadas
            # Esto permite generar reglas incluso sin eventos de red
            synthetic_events = self._generate_synthetic_events_from_metrics()
            if synthetic_events:
                print(f"      ✅ Generados {len(synthetic_events)} eventos sintéticos basados en métricas")
                events = synthetic_events
            else:
                print(f"      ❌ No se pueden generar reglas sin contexto")
                return
        
        print(f"      ✅ Eventos encontrados: {len(events)} eventos relevantes")
        print(f"      📊 Tipos de eventos: {', '.join(set(e.get('event_type', 'unknown') for e in events))}")
        print(f"      📤 Estos eventos se enviarán al analizador para análisis y generación de reglas")
        
        # Generar reglas con el analizador local
        print(f"\n[3.3] 🔍 Analizando eventos y generando reglas...")
        print(f"      📝 Eventos a analizar: {len(events)}")
        
        parsed_rules = self.generate_rules_with_analyzer(events)
        
        if not parsed_rules:
            print(f"      ❌ ERROR: No se pudieron generar reglas")
            print(f"      💡 El analizador no detectó patrones de amenazas en los eventos")
            return
        
        print(f"      ✅ Reglas generadas: {len(parsed_rules)} reglas listas para enviar")
        
        # Guardar en archivo de Suricata (para que Suricata las use)
        print(f"\n[3.4] 💾 Guardando reglas en archivo de Suricata...")
        rules_text = self.eve_analyzer.get_rules_text()
        self.save_rules_to_suricata_file(rules_text)
        print(f"      ✅ Reglas guardadas en: {self.suricata_rules_file}")
        
        # Guardar en archivo (backup)
        print(f"\n[3.5] 💾 Guardando reglas en archivo (backup)...")
        self.save_rules_to_file(rules_text)
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
        print(f"[INFO] Archivo de reglas (backup): {self.rules_file}")
        print(f"[INFO] Archivo de reglas de Suricata: {self.suricata_rules_file}")
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
        help=f'Archivo donde guardar las reglas (backup) (default: {DEFAULT_RULES_FILE})'
    )
    
    parser.add_argument(
        '--suricata-rules-file',
        type=str,
        default=DEFAULT_SURICATA_RULES_FILE,
        help=f'Archivo de reglas de Suricata donde escribir las reglas (default: {DEFAULT_SURICATA_RULES_FILE})'
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
        suricata_rules_file=args.suricata_rules_file,
        interval=args.interval,
        backend_url=args.backend_url
    )
    
    monitor.run()


if __name__ == "__main__":
    main()

