// src/application/use-cases/detect-cryptojacking.usecase.ts
import { Inject, Injectable } from '@nestjs/common';
import { RuleRepository } from '../../domain/repositories/rule.repository';
import { AlertRepository } from '../../domain/repositories/alert.repository';
import { CryptoDetectionService } from '../../domain/services/crypto-detection.service';
import { TOKENS } from '../token';
import { EventEntity } from '../../domain/entities/event.entity';
import { AlertEntity } from '../../domain/entities/alert.entity';
import { randomUUID } from 'crypto';

@Injectable()
export class DetectCryptojackingUseCase {
  constructor(
    private readonly detector: CryptoDetectionService,
    @Inject(TOKENS.RuleRepo)
    private readonly rules: RuleRepository,
    @Inject(TOKENS.AlertRepo)
    private readonly alerts: AlertRepository,
    @Inject(TOKENS.NatsPub)
    private readonly publish: (subject: string, payload: any) => Promise<void>,
  ) {}

async exec(event: EventEntity): Promise<AlertEntity | null> {
  const rules = await this.rules.listEnabled();

  if (!rules || rules.length === 0) {
    return null;
  }

  const hits = this.detector.detect(event, rules);
  if (hits.length === 0) {
    return null;
  }

  const alert = new AlertEntity(
    randomUUID(),
    event.id,  // o flowId/eventId según cómo dejemos el modelo Alert
    'high',
    {
      ruleHits: hits,
      sni: event.getSni(),
      kind: event.kind,
    },
    new Date(),
  );

  await this.alerts.create(alert);
  await this.publish('alerts.detector', { ...alert });

  return alert;
}
}
