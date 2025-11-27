// src/interfaces/http/rules.controller.ts
import { Controller, Get, Post, Body, Patch, Param } from '@nestjs/common';
import { RuleRepository } from '../../domain/repositories/rule.repository';
import { CreateRuleDto } from '../dto/create-rule.dto';
import { RuleEntity } from '../../domain/entities/rule.entity';
import { randomUUID } from 'crypto';

@Controller('rules')
export class RulesController {
  constructor(private readonly rules: RuleRepository) {}

  @Get()
  async list() {
    return this.rules.listEnabled();
  }

  @Post()
async create(@Body() dto: CreateRuleDto) {
  const id = randomUUID();

  const r = new RuleEntity(
    id,
    'DOMAIN_IOC',                        // type requerido por Prisma
    dto.name ?? dto.body ?? 'unknown',   // pattern requerido (obligatorio)
    null,                                // description (nullable, por ahora null)
    dto.enabled ?? true,
    dto.tags ?? [],
    dto.vendor ?? null,
    dto.sid ?? null,
    dto.name ?? null,
    dto.body ?? null,
  );

  return this.rules.create(r);
}

  @Patch(':id/:enabled')
  async toggle(@Param('id') id: string, @Param('enabled') enabled: string) {
    await this.rules.toggle(id, enabled === 'true');
    return { ok: true };
  }
}

