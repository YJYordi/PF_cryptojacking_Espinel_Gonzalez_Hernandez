import { EventEntity } from '../entities/event.entity';
import { RuleEntity } from '../entities/rule.entity';

export class CryptoDetectionService {
  detect(event: EventEntity, rules: RuleEntity[]): string[] {
    const hits: string[] = [];
    const sni = event.getSni();
    const dnsRrname = event.getDnsRrname();
    const httpHostname = event.getHttpHostname();
    const httpUrl = event.getHttpUrl();
    const httpUserAgent = event.getHttpUserAgent();

    for (const r of rules.filter(r => r.enabled)) {
      if (r.type === 'DOMAIN_IOC') {
        // Detectar en TLS SNI
        if (sni && sni.toLowerCase().includes(r.pattern.toLowerCase())) {
          hits.push(`TLS SNI IOC match: ${r.pattern}`);
        }
        
        // Detectar en DNS rrname
        if (dnsRrname && dnsRrname.toLowerCase().includes(r.pattern.toLowerCase())) {
          hits.push(`DNS IOC match: ${r.pattern}`);
        }
        
        // Detectar en HTTP hostname
        if (httpHostname && httpHostname.toLowerCase().includes(r.pattern.toLowerCase())) {
          hits.push(`HTTP Hostname IOC match: ${r.pattern}`);
        }
        
        // Detectar en HTTP URL
        if (httpUrl && httpUrl.toLowerCase().includes(r.pattern.toLowerCase())) {
          hits.push(`HTTP URL IOC match: ${r.pattern}`);
        }
        
        // Detectar en HTTP User Agent
        if (httpUserAgent && httpUserAgent.toLowerCase().includes(r.pattern.toLowerCase())) {
          hits.push(`HTTP User Agent IOC match: ${r.pattern}`);
        }
      }
      // aquí puedes extender: JA3, PROCESS, THRESHOLD...
    }
    return hits;
  }
}
