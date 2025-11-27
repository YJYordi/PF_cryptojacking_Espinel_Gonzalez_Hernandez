import { Body, Controller, Post } from '@nestjs/common';
import { IngestEveDto } from '../dto/ingest-eve.dto';
import { IngestEventsUseCase } from '../../application/use-cases/ingest-events.usecase';

@Controller('ingest')
export class IngestController {
  constructor(private readonly ingestUC: IngestEventsUseCase) {}

  @Post('eve')
  async ingestEve(@Body() dto: IngestEveDto) {
    const n = await this.ingestUC.exec(dto.host_id, dto.events);
    return { ok: true, n };
  }
}
