import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { EventRepository } from '../../domain/repositories/event.repository';
import { EventEntity } from '../../domain/entities/event.entity';

@Injectable()
export class PrismaEventRepository implements EventRepository {
  constructor(private prisma: PrismaService) {}
  async saveMany(events: EventEntity[]): Promise<void> {
    await this.prisma.$transaction(events.map(e => this.prisma.event.create({
      data: { id: e.id, hostId: e.hostId, kind: e.kind, ts: e.ts, payload: e.payload as any },
    })));
  }
  async findRecent(limit = 50): Promise<EventEntity[]> {
    const rows = await this.prisma.event.findMany({ take: limit, orderBy: { ts: 'desc' } });
    return rows.map((r: { id: string; hostId: string; kind: string; ts: Date; payload: unknown }) => 
      new EventEntity(r.id, r.hostId, r.kind, r.ts, r.payload as any)
    );
  }
}
