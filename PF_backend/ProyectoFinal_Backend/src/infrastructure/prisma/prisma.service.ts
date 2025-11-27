import { INestApplication, Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  async onModuleInit() {
    await this.$connect();
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }

  async enableShutdownHooks(app: INestApplication) {
    // En Prisma 5.0.0+, usar eventos del proceso directamente
    // No usar $on() hooks que ya no son compatibles con library engine
    process.on('beforeExit', async () => {
      await app.close();
    });
  }
}
