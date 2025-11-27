import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { HostRepository } from '../../domain/repositories/host.repository';
import { HostEntity } from '../../domain/entities/host.entity';

@Injectable()
export class PrismaHostRepository extends HostRepository {
  constructor(private readonly prisma: PrismaService) {
    super();
  }

  async findById(id: string): Promise<HostEntity | null> {
    const row = await this.prisma.host.findUnique({ where: { id } });
    if (!row) return null;
    return this.mapRow(row);
  }

  async upsert(id: string, name?: string): Promise<HostEntity> {
    const row = await this.prisma.host.upsert({
      where: { id },
      create: {
        id,
        name: name ?? id,
        labels: {},            // Host.labels es Json obligatorio
        lastSeen: new Date(),
      },
      update: {
        name: name ?? id,
        lastSeen: new Date(),
      },
    });

    return this.mapRow(row);
  }

  async list(): Promise<HostEntity[]> {
    const rows = await this.prisma.host.findMany({
      orderBy: { lastSeen: 'desc' },
    });

    return rows.map((r: { id: string; name: string; createdAt: Date; lastSeen: Date; labels: unknown }) => this.mapRow(r));
  }

  private mapRow(row: {
    id: string;
    name: string;
    createdAt: Date;
    lastSeen: Date;
    labels: unknown;
  }): HostEntity {
    return new HostEntity(row.id, row.name, row.createdAt, row.lastSeen, row.labels);
  }
}
