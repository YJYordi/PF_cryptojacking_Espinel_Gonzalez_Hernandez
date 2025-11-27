// src/infrastructure/repositories/prisma-alert.repository.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { AlertEntity } from '../../domain/entities/alert.entity';
import { Prisma } from '@prisma/client';
import { AlertRepository } from '../../domain/repositories/alert.repository';

@Injectable()
export class PrismaAlertRepository implements AlertRepository {
  constructor(private readonly prisma: PrismaService) {}

  /** Crear alerta */
  async create(alert: AlertEntity): Promise<AlertEntity> {
    const result = await this.prisma.alert.create({
      data: {
        id: alert.id,
        eventId: alert.eventId, // 👈 YA NO flowId
        severity: alert.severity,
        reason: alert.reason as any,
      },
    });

    return new AlertEntity(
      result.id,
      result.eventId,
      result.severity as 'low' | 'med' | 'high',
      result.reason,
      result.createdAt,
    );
  }

  async findRecent(limit = 20): Promise<AlertEntity[]> {
    const rows = await this.prisma.alert.findMany({
      orderBy: { createdAt: 'desc' },
      take: limit,
    });

    return rows.map(
      (r: { id: string; eventId: string; severity: string; reason: unknown; createdAt: Date }) =>
        new AlertEntity(
          r.id,
          r.eventId,
          r.severity as 'low' | 'med' | 'high',
          r.reason,
          r.createdAt,
        ),
    );
  }

  async findByEvent(eventId: string): Promise<AlertEntity[]> {
    const rows = await this.prisma.alert.findMany({
      where: { eventId },
      orderBy: { createdAt: 'desc' },
    });

    return rows.map(
      (r: { id: string; eventId: string; severity: string; reason: unknown; createdAt: Date }) =>
        new AlertEntity(
          r.id,
          r.eventId,
          r.severity as 'low' | 'med' | 'high',
          r.reason,
          r.createdAt,
        ),
    );
  }
}
