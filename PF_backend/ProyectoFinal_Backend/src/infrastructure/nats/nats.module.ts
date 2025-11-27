import { Module, Global } from '@nestjs/common';
import { NatsService } from './nats.service';

@Global() // Hace disponible NatsService en toda la app sin re-importar
@Module({
  providers: [NatsService],
  exports: [NatsService],
})
export class NatsModule {}
