import { NestFactory } from '@nestjs/core';
import { DetectorModule } from './infrastructure/workers/detector/detector.module';

async function bootstrap() {
  const app = await NestFactory.createApplicationContext(DetectorModule, { logger: ['log','error','warn'] });
  // queda corriendo como proceso worker
}
bootstrap();
