import { Inject, Injectable } from '@nestjs/common';
import { EventRepository } from '../../domain/repositories/event.repository';
import { HostRepository } from '../../domain/repositories/host.repository';
import { TOKENS } from '../token';
import { EventEntity } from '../../domain/entities/event.entity';
import { randomUUID } from 'crypto';
import { appendFile, mkdir } from 'fs/promises';
import { dirname } from 'path';

@Injectable()
export class IngestEventsUseCase {
  private readonly eveJsonPath: string;

  constructor(
    @Inject(TOKENS.EventRepo) private readonly events: EventRepository,
    @Inject(TOKENS.HostRepo)  private readonly hosts: HostRepository,
    @Inject(TOKENS.NatsPub)   private readonly publish: (s: string, p: any)=>Promise<void>,
  ) {
    // Ruta del eve.json (configurable por variable de entorno)
    this.eveJsonPath = process.env.EVE_JSON_PATH || '/var/log/suricata/eve.json';
  }

  /**
   * Escribe eventos en formato eve.json (una línea JSON por evento)
   * Formato compatible con Suricata para que el pipeline ML los pueda leer
   */
  private async writeToEveJson(events: any[]): Promise<void> {
    try {
      // Crear directorio si no existe
      await mkdir(dirname(this.eveJsonPath), { recursive: true });

      // Escribir cada evento como una línea JSON (formato eve.json)
      for (const event of events) {
        const jsonLine = JSON.stringify(event) + '\n';
        await appendFile(this.eveJsonPath, jsonLine, 'utf-8');
      }
    } catch (error) {
      // No fallar si no se puede escribir en eve.json (puede no estar montado)
      console.warn(`[WARNING] No se pudo escribir en ${this.eveJsonPath}:`, error);
    }
  }

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
    
    // Escribir eventos en eve.json para que el pipeline ML los pueda leer
    await this.writeToEveJson(rawEvents);

    return entities.length;
  }
}
