import { RuleEntity } from '../entities/rule.entity';

export abstract class RuleRepository {
  abstract listEnabled(): Promise<RuleEntity[]>;
  abstract create(rule: RuleEntity): Promise<RuleEntity>;
  abstract toggle(id: string, enabled: boolean): Promise<void>;
}
