import { EventEntity } from '../entities/event.entity';
import { RuleEntity } from '../entities/rule.entity';

export class CryptoDetectionService {
  detect(event: EventEntity, rules: RuleEntity[]): string[] {
    const hits: string[] = [];
    const sni = event.getSni();

    for (const r of rules.filter(r => r.enabled)) {
      if (r.type === 'DOMAIN_IOC' && sni && sni.includes(r.pattern)) {
        hits.push(`SNI IOC match: ${r.pattern}`);
      }
      // aquí puedes extender: JA3, PROCESS, THRESHOLD...
    }
    return hits;
  }
}
