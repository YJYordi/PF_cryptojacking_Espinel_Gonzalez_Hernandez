import { Module } from '@nestjs/common';
import { PrismaModule } from '../../prisma/prisma.module';
import { NatsModule } from '../../nats/nats.module';
import { DetectorSubscriber } from './detector.subscriber';
import { DetectCryptojackingUseCase } from '../../../application/use-cases/detect-cryptojacking.usecase';
import { CryptoDetectionService } from '../../../domain/services/crypto-detection.service';
import { TOKENS } from '../../../application/token';
import { PrismaEventRepository } from '../../repositories/prisma-event.repository';
import { PrismaRuleRepository } from '../../repositories/prisma-rule.repository';
import { PrismaAlertRepository } from '../../repositories/prisma-alert.repository';
import { EventRepository } from '../../../domain/repositories/event.repository'; 
import { RuleRepository } from '../../../domain/repositories/rule.repository'; 
import { AlertRepository } from '../../../domain/repositories/alert.repository';
import { NatsService } from '../../nats/nats.service';

@Module({
  imports: [PrismaModule, NatsModule],
  providers: [
    DetectorSubscriber,
    DetectCryptojackingUseCase,
    CryptoDetectionService,
    { provide: TOKENS.EventRepo, useClass: PrismaEventRepository },
    { provide: TOKENS.RuleRepo,  useClass: PrismaRuleRepository },
    { provide: TOKENS.AlertRepo, useClass: PrismaAlertRepository },
    { provide: TOKENS.NatsPub,   useFactory: (n: NatsService) => n.publish.bind(n), inject: [NatsService] },
  ],
})
export class DetectorModule {}

