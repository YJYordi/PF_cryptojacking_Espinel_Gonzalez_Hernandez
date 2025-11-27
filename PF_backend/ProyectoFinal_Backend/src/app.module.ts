import { Module } from '@nestjs/common';
import { PrismaModule } from './infrastructure/prisma/prisma.module';
import { NatsModule } from './infrastructure/nats/nats.module';

import { TOKENS } from './application/token';
import { NatsService } from './infrastructure/nats/nats.service';

import { PrismaEventRepository } from './infrastructure/repositories/prisma-event.repository';
import { PrismaHostRepository } from './infrastructure/repositories/prisma-host.repository';
import { IngestEventsUseCase } from './application/use-cases/ingest-events.usecase';
import { IngestController } from './interfaces/http/ingest.controller';
import { RulesController } from './interfaces/http/rules.controller';
import { PrismaRuleRepository } from './infrastructure/repositories/prisma-rule.repository';
import { RuleRepository } from './domain/repositories/rule.repository';


@Module({
  imports: [PrismaModule, NatsModule],
  controllers: [IngestController, RulesController],
  providers: [
    IngestEventsUseCase,

    { provide: TOKENS.EventRepo, useClass: PrismaEventRepository },
    { provide: TOKENS.HostRepo,  useClass: PrismaHostRepository },
    { provide: RuleRepository, useClass: PrismaRuleRepository },

    {
      provide: TOKENS.NatsPub,
      useFactory: (nats: NatsService) => nats.publish.bind(nats),
      inject: [NatsService],
    },
  ],
})
export class AppModule {}
