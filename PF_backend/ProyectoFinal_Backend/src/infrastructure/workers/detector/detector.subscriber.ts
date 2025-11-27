import { Injectable, OnModuleInit } from '@nestjs/common';
import { NatsService } from '../../nats/nats.service';
import { DetectCryptojackingUseCase } from '../../../application/use-cases/detect-cryptojacking.usecase';
import { EventEntity } from '../../../domain/entities/event.entity';
import { randomUUID } from 'crypto';

@Injectable()
export class DetectorSubscriber implements OnModuleInit {
  constructor(
    private readonly nats: NatsService,
    private readonly detectUC: DetectCryptojackingUseCase,
  ) {}

  async onModuleInit() {
    await this.nats.subscribe('eve.suricata', async (msg: any) => {
      const hostId = msg.host_id;
      for (const ev of msg.events ?? []) {
        // Usar el ID del evento que viene del mensaje (si existe) o generar uno nuevo
        const eventId = ev.id || randomUUID();
        const entity = new EventEntity(
          eventId,
          hostId,
          ev.event_type || 'unknown',
          new Date(),
          ev,
        );
        await this.detectUC.exec(entity);
      }
    });
    console.log('[detector] suscripto a eve.suricata');
  }
}

