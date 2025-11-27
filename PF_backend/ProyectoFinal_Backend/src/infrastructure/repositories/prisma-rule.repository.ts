// src/infrastructure/repositories/prisma-rule.repository.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { RuleEntity } from '../../domain/entities/rule.entity';
import { RuleRepository } from '../../domain/repositories/rule.repository';

@Injectable()
export class PrismaRuleRepository extends RuleRepository {
  constructor(private readonly prisma: PrismaService) {
    super();
  }

  /** Devuelve solo las reglas habilitadas */
  async listEnabled(): Promise<RuleEntity[]> {
    const rows = await this.prisma.rule.findMany({
      where: { enabled: true },
      orderBy: { createdAt: 'desc' }, // opcional, pero útil
    });

    return rows.map(
      (r: { id: string; type: string; pattern: string; description: string | null; enabled: boolean; tags: string[]; vendor: string | null; sid: number | null; name: string | null; body: string | null }) =>
        new RuleEntity(
          r.id,
          r.type,
          r.pattern,
          r.description,
          r.enabled,
          r.tags,
          r.vendor ?? null,
          r.sid ?? null,
          r.name ?? null,
          r.body ?? null,
        ),
    );
  }

  /** Crea una nueva regla */
  async create(rule: RuleEntity): Promise<RuleEntity> {
    const created = await this.prisma.rule.create({
      data: {
        id: rule.id,                // si quieres dejar que Prisma genere el id, puedes omitirlo
        type: rule.type,
        pattern: rule.pattern,
        description: rule.description,
        enabled: rule.enabled,
        tags: rule.tags,
        vendor: rule.vendor ?? null,
        sid: rule.sid ?? null,
        name: rule.name ?? null,
        body: rule.body ?? null,
      },
    });

    return new RuleEntity(
      created.id,
      created.type,
      created.pattern,
      created.description,
      created.enabled,
      created.tags,
      created.vendor ?? null,
      created.sid ?? null,
      created.name ?? null,
      created.body ?? null,
    );
  }

  /** Habilitar / deshabilitar regla */
  async toggle(id: string, enabled: boolean): Promise<void> {
    await this.prisma.rule.update({
      where: { id },
      data: { enabled },
    });
  }
}
