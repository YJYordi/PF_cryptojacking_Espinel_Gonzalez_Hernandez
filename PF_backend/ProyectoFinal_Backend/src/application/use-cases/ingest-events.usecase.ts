import { Inject, Injectable } from '@nestjs/common';
import { EventRepository } from '../../domain/repositories/event.repository';
import { HostRepository } from '../../domain/repositories/host.repository';
import { TOKENS } from '../token';
import { EventEntity } from '../../domain/entities/event.entity';
import { randomUUID } from 'crypto';

@Injectable()
export class IngestEventsUseCase {
  constructor(
    @Inject(TOKENS.EventRepo) private readonly events: EventRepository,
    @Inject(TOKENS.HostRepo)  private readonly hosts: HostRepository,
    @Inject(TOKENS.NatsPub)   private readonly publish: (s: string, p: any)=>Promise<void>,
  ) {}

  async exec(hostId: string, rawEvents: any[]) {
    // upsert host vía repositorio de dominio
    await this.hosts.upsert(hostId);

    const entities = rawEvents.map(ev =>
      new EventEntity(
        randomUUID(),
        hostId,
        ev.event_type || 'unknown',
        new Date(),
        ev,
      ),
    );

    await this.events.saveMany(entities);
    await this.publish('eve.suricata', { host_id: hostId, events: rawEvents });

    return entities.length;
  }
}
