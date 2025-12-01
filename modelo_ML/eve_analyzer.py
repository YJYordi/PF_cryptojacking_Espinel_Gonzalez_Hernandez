#!/usr/bin/env python3
"""
Analizador de eventos EVE.json para generar reglas de Suricata automáticamente.
Detecta patrones de amenazas (cryptojacking, minería, etc.) y genera reglas correspondientes.
"""

import re
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict
from datetime import datetime


class EVEAnalyzer:
    """Analizador de eventos EVE que genera reglas de Suricata automáticamente."""
    
    # Patrones de amenazas conocidas
    MINING_POOLS = {
        'pool.minexmr.com', 'pool.supportxmr.com', 'pool.hashvault.pro',
        'xmrpool.eu', 'monero.hashvault.pro', 'minexmr.com',
        'pool.cryptonote.social', 'pool.nimiq.com', 'ethpool.org',
        'ethermine.org', 'f2pool.com', 'nanopool.org'
    }
    
    MINING_USER_AGENTS = [
        'xmrig', 'xmr-stak', 'cpuminer', 'minerd', 'ccminer',
        'cudaminer', 'ethminer', 'claymore', 'phoenixminer',
        'nbminer', 'trex', 'lolminer', 'teamredminer'
    ]
    
    MINING_PATHS = [
        '/api/v1/work', '/api/v1/submit', '/api/v1/job',
        '/stratum', '/mining', '/pool', '/submit', '/work',
        '/getwork', '/getjob', '/login', '/subscribe'
    ]
    
    SUSPICIOUS_PORTS = [3333, 4444, 5555, 8080, 8888, 9999, 14444, 14433]
    
    def __init__(self, base_sid: int = 2000000):
        """
        Inicializa el analizador.
        
        Args:
            base_sid: SID base para las reglas generadas (default: 2000000)
        """
        self.base_sid = base_sid
        self.rule_counter = 0
        self.generated_rules: List[Dict[str, Any]] = []
    
    def analyze_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analiza eventos EVE y genera reglas de Suricata.
        
        Args:
            events: Lista de eventos EVE.json
        
        Returns:
            Lista de reglas generadas en formato para el backend
        """
        if not events:
            return []
        
        self.generated_rules = []
        self.rule_counter = 0
        
        # Agrupar eventos por tipo para análisis
        events_by_type = defaultdict(list)
        for event in events:
            event_type = event.get('event_type', 'unknown')
            events_by_type[event_type].append(event)
        
        print(f"      📊 Analizando {len(events)} eventos...")
        print(f"      📋 Tipos de eventos: {', '.join(events_by_type.keys())}")
        
        # Analizar diferentes tipos de eventos
        self._analyze_http_events(events_by_type.get('http', []))
        self._analyze_flow_events(events_by_type.get('flow', []))
        self._analyze_dns_events(events_by_type.get('dns', []))
        self._analyze_tls_events(events_by_type.get('tls', []))
        self._analyze_alert_events(events_by_type.get('alert', []))
        
        # Analizar patrones cruzados
        self._analyze_cross_patterns(events)
        
        print(f"      ✅ Reglas generadas: {len(self.generated_rules)}")
        return self.generated_rules
    
    def _analyze_http_events(self, http_events: List[Dict[str, Any]]) -> None:
        """Analiza eventos HTTP y genera reglas para patrones sospechosos."""
        if not http_events:
            return
        
        # Agrupar por hostname y URL
        hostname_patterns = defaultdict(list)
        url_patterns = defaultdict(list)
        user_agents = defaultdict(int)
        
        for event in http_events:
            http_data = event.get('http', {})
            hostname = http_data.get('hostname', '')
            url = http_data.get('url', '')
            user_agent = http_data.get('http_user_agent', '')
            
            if hostname:
                hostname_patterns[hostname].append(event)
            if url:
                url_patterns[url].append(event)
            if user_agent:
                user_agents[user_agent.lower()] += 1
        
        # Detectar pools de minería por hostname
        for hostname, events_list in hostname_patterns.items():
            if self._is_mining_pool(hostname):
                rule = self._create_mining_pool_rule(hostname, events_list)
                if rule:
                    self.generated_rules.append(rule)
        
        # Detectar user agents de mineros
        for user_agent, count in user_agents.items():
            if self._is_mining_user_agent(user_agent):
                rule = self._create_mining_user_agent_rule(user_agent, count)
                if rule:
                    self.generated_rules.append(rule)
        
        # Detectar URLs sospechosas de minería
        for url, events_list in url_patterns.items():
            if self._is_mining_path(url):
                rule = self._create_mining_path_rule(url, events_list)
                if rule:
                    self.generated_rules.append(rule)
    
    def _analyze_flow_events(self, flow_events: List[Dict[str, Any]]) -> None:
        """Analiza eventos de flujo y genera reglas para tráfico sospechoso."""
        if not flow_events:
            return
        
        # Detectar flujos con alto volumen de datos (posible minería)
        for event in flow_events:
            flow_data = event.get('flow', {})
            bytes_toserver = flow_data.get('bytes_toserver', 0)
            bytes_toclient = flow_data.get('bytes_toclient', 0)
            total_bytes = bytes_toserver + bytes_toclient
            
            # Si hay mucho tráfico a un puerto sospechoso
            dest_port = event.get('dest_port', 0)
            if total_bytes > 100000 and dest_port in self.SUSPICIOUS_PORTS:
                rule = self._create_high_volume_rule(event, total_bytes)
                if rule:
                    self.generated_rules.append(rule)
    
    def _analyze_dns_events(self, dns_events: List[Dict[str, Any]]) -> None:
        """Analiza eventos DNS y genera reglas para dominios sospechosos."""
        if not dns_events:
            return
        
        # Detectar consultas DNS a pools de minería
        for event in dns_events:
            dns_data = event.get('dns', {})
            rrtype = dns_data.get('rrtype', '')
            
            if rrtype == 'A' or rrtype == 'AAAA':
                answers = dns_data.get('answers', [])
                for answer in answers:
                    rdata = answer.get('rdata', '')
                    if self._is_mining_pool(rdata):
                        rule = self._create_dns_mining_rule(event, rdata)
                        if rule:
                            self.generated_rules.append(rule)
    
    def _analyze_tls_events(self, tls_events: List[Dict[str, Any]]) -> None:
        """Analiza eventos TLS y genera reglas para SNI sospechosos."""
        if not tls_events:
            return
        
        # Detectar SNI (Server Name Indication) de pools de minería
        for event in tls_events:
            tls_data = event.get('tls', {})
            sni = tls_data.get('sni', '')
            
            if sni and self._is_mining_pool(sni):
                rule = self._create_tls_mining_rule(event, sni)
                if rule:
                    self.generated_rules.append(rule)
    
    def _analyze_alert_events(self, alert_events: List[Dict[str, Any]]) -> None:
        """Analiza eventos de alerta existentes para evitar duplicados."""
        # Si ya hay alertas, no generar reglas redundantes
        if alert_events:
            print(f"      ℹ️  Se encontraron {len(alert_events)} alertas existentes")
    
    def _analyze_cross_patterns(self, events: List[Dict[str, Any]]) -> None:
        """Analiza patrones cruzados entre diferentes tipos de eventos."""
        # Detectar conexiones persistentes a IPs sospechosas
        ip_connections = defaultdict(int)
        ip_ports = defaultdict(set)
        
        for event in events:
            dest_ip = event.get('dest_ip', '')
            dest_port = event.get('dest_port', 0)
            
            if dest_ip and dest_port:
                ip_connections[dest_ip] += 1
                ip_ports[dest_ip].add(dest_port)
        
        # Si hay muchas conexiones a la misma IP en puertos sospechosos
        for ip, count in ip_connections.items():
            if count > 10 and any(p in self.SUSPICIOUS_PORTS for p in ip_ports[ip]):
                rule = self._create_suspicious_ip_rule(ip, count, ip_ports[ip])
                if rule:
                    self.generated_rules.append(rule)
    
    def _is_mining_pool(self, hostname: str) -> bool:
        """Verifica si un hostname es un pool de minería conocido."""
        hostname_lower = hostname.lower()
        return any(pool in hostname_lower for pool in self.MINING_POOLS)
    
    def _is_mining_user_agent(self, user_agent: str) -> bool:
        """Verifica si un user agent es de un minero conocido."""
        user_agent_lower = user_agent.lower()
        return any(agent in user_agent_lower for agent in self.MINING_USER_AGENTS)
    
    def _is_mining_path(self, url: str) -> bool:
        """Verifica si una URL es un endpoint de minería."""
        url_lower = url.lower()
        return any(path in url_lower for path in self.MINING_PATHS)
    
    def _create_mining_pool_rule(self, hostname: str, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Crea una regla para bloquear tráfico a un pool de minería."""
        if not events:
            return None
        
        # Obtener IPs y puertos del primer evento
        first_event = events[0]
        dest_ip = first_event.get('dest_ip', 'any')
        dest_port = first_event.get('dest_port', 'any')
        proto = first_event.get('proto', 'TCP')
        
        self.rule_counter += 1
        sid = self.base_sid + self.rule_counter
        
        rule_body = f'alert {proto} any any -> {dest_ip} {dest_port} (msg:"Cryptojacking: Conexión a pool de minería {hostname}"; flow:established,to_server; content:"{hostname}"; http_host; sid:{sid}; rev:1;)'
        
        return {
            'vendor': 'suricata',
            'sid': sid,
            'name': f'Cryptojacking: Pool de minería {hostname}',
            'body': rule_body,
            'tags': ['auto-generated', 'cryptojacking', 'mining-pool'],
            'enabled': True
        }
    
    def _create_mining_user_agent_rule(self, user_agent: str, count: int) -> Optional[Dict[str, Any]]:
        """Crea una regla para detectar user agents de mineros."""
        # Extraer el nombre del minero del user agent
        miner_name = 'Unknown'
        for agent in self.MINING_USER_AGENTS:
            if agent in user_agent.lower():
                miner_name = agent.upper()
                break
        
        self.rule_counter += 1
        sid = self.base_sid + self.rule_counter
        
        # Escapar caracteres especiales para content
        user_agent_escaped = user_agent.replace('"', '\\"').replace(';', '\\;')
        
        rule_body = f'alert http any any -> any any (msg:"Cryptojacking: User agent de minero detectado - {miner_name}"; flow:established,to_server; content:"{user_agent_escaped}"; http_user_agent; sid:{sid}; rev:1;)'
        
        return {
            'vendor': 'suricata',
            'sid': sid,
            'name': f'Cryptojacking: Minero {miner_name} detectado',
            'body': rule_body,
            'tags': ['auto-generated', 'cryptojacking', 'miner-detection'],
            'enabled': True
        }
    
    def _create_mining_path_rule(self, url: str, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Crea una regla para detectar endpoints de minería."""
        if not events:
            return None
        
        first_event = events[0]
        proto = first_event.get('proto', 'TCP')
        
        self.rule_counter += 1
        sid = self.base_sid + self.rule_counter
        
        # Escapar URL para content
        url_escaped = url.replace('"', '\\"').replace(';', '\\;')
        
        rule_body = f'alert {proto} any any -> any any (msg:"Cryptojacking: Endpoint de minería detectado - {url}"; flow:established,to_server; content:"{url_escaped}"; http_uri; sid:{sid}; rev:1;)'
        
        return {
            'vendor': 'suricata',
            'sid': sid,
            'name': f'Cryptojacking: Endpoint de minería {url}',
            'body': rule_body,
            'tags': ['auto-generated', 'cryptojacking', 'mining-endpoint'],
            'enabled': True
        }
    
    def _create_high_volume_rule(self, event: Dict[str, Any], total_bytes: int) -> Optional[Dict[str, Any]]:
        """Crea una regla para detectar tráfico de alto volumen sospechoso."""
        dest_ip = event.get('dest_ip', 'any')
        dest_port = event.get('dest_port', 'any')
        proto = event.get('proto', 'TCP')
        
        self.rule_counter += 1
        sid = self.base_sid + self.rule_counter
        
        rule_body = f'alert {proto} any any -> {dest_ip} {dest_port} (msg:"Cryptojacking: Tráfico de alto volumen sospechoso ({total_bytes} bytes)"; flow:established,to_server; threshold:type limit, track by_src, count 5, seconds 60; sid:{sid}; rev:1;)'
        
        return {
            'vendor': 'suricata',
            'sid': sid,
            'name': f'Cryptojacking: Tráfico sospechoso alto volumen a {dest_ip}:{dest_port}',
            'body': rule_body,
            'tags': ['auto-generated', 'cryptojacking', 'high-volume'],
            'enabled': True
        }
    
    def _create_dns_mining_rule(self, event: Dict[str, Any], rdata: str) -> Optional[Dict[str, Any]]:
        """Crea una regla para detectar consultas DNS a pools de minería."""
        self.rule_counter += 1
        sid = self.base_sid + self.rule_counter
        
        rule_body = f'alert dns any any -> any 53 (msg:"Cryptojacking: Consulta DNS a pool de minería {rdata}"; dns_query; content:"{rdata}"; sid:{sid}; rev:1;)'
        
        return {
            'vendor': 'suricata',
            'sid': sid,
            'name': f'Cryptojacking: DNS a pool de minería {rdata}',
            'body': rule_body,
            'tags': ['auto-generated', 'cryptojacking', 'dns-mining'],
            'enabled': True
        }
    
    def _create_tls_mining_rule(self, event: Dict[str, Any], sni: str) -> Optional[Dict[str, Any]]:
        """Crea una regla para detectar SNI de pools de minería."""
        dest_ip = event.get('dest_ip', 'any')
        dest_port = event.get('dest_port', 443)
        
        self.rule_counter += 1
        sid = self.base_sid + self.rule_counter
        
        rule_body = f'alert tls any any -> {dest_ip} {dest_port} (msg:"Cryptojacking: SNI de pool de minería {sni}"; tls_sni; content:"{sni}"; sid:{sid}; rev:1;)'
        
        return {
            'vendor': 'suricata',
            'sid': sid,
            'name': f'Cryptojacking: TLS SNI a pool de minería {sni}',
            'body': rule_body,
            'tags': ['auto-generated', 'cryptojacking', 'tls-mining'],
            'enabled': True
        }
    
    def _create_suspicious_ip_rule(self, ip: str, connection_count: int, ports: Set[int]) -> Optional[Dict[str, Any]]:
        """Crea una regla para detectar múltiples conexiones a IPs sospechosas."""
        ports_str = ','.join(map(str, sorted(ports)))
        
        self.rule_counter += 1
        sid = self.base_sid + self.rule_counter
        
        rule_body = f'alert tcp any any -> {ip} any (msg:"Cryptojacking: Múltiples conexiones sospechosas a {ip} (puertos: {ports_str})"; flow:established,to_server; threshold:type limit, track by_src, count {connection_count}, seconds 60; sid:{sid}; rev:1;)'
        
        return {
            'vendor': 'suricata',
            'sid': sid,
            'name': f'Cryptojacking: IP sospechosa {ip} con {connection_count} conexiones',
            'body': rule_body,
            'tags': ['auto-generated', 'cryptojacking', 'suspicious-ip'],
            'enabled': True
        }
    
    def get_rules_text(self) -> str:
        """
        Obtiene las reglas generadas en formato de texto para guardar en archivo.
        
        Returns:
            Texto con todas las reglas generadas
        """
        if not self.generated_rules:
            return ""
        
        lines = []
        lines.append("# Reglas generadas automáticamente por EVE Analyzer")
        lines.append(f"# Generadas el: {datetime.now().isoformat()}")
        lines.append(f"# Total de reglas: {len(self.generated_rules)}")
        lines.append("")
        
        for rule in self.generated_rules:
            lines.append(f"# {rule['name']}")
            lines.append(rule['body'])
            lines.append("")
        
        return "\n".join(lines)

