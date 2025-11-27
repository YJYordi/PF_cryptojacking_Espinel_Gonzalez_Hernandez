import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
import { connect, NatsConnection, StringCodec, Subscription } from 'nats';

@Injectable()
export class NatsService implements OnModuleInit, OnModuleDestroy {
  private nc: NatsConnection;
  private logger = new Logger(NatsService.name);
  private sc = StringCodec();

  async onModuleInit() {
    this.logger.log('🔌 Connecting to NATS...');

    this.nc = await connect({
      servers: process.env.NATS_URL || 'nats://nats:4222',
    });

    this.logger.log(`✅ Connected to NATS: ${this.nc.getServer()}`);
  }

  async onModuleDestroy() {
    this.logger.log('🔌 Closing NATS connection...');
    await this.nc?.close();
  }

  /** ---- PUBLISH ---- */
  async publish(subject: string, payload: any) {
    const data = typeof payload === 'string' ? payload : JSON.stringify(payload);
    this.nc.publish(subject, this.sc.encode(data));
  }

  /** ---- OPTIONAL: Simple subscribe ---- */
  subscribe(subject: string, handler: (msg: any) => void): Subscription {
    const sub = this.nc.subscribe(subject);

    (async () => {
      for await (const m of sub) {
        const decoded = this.sc.decode(m.data);
        handler(JSON.parse(decoded));
      }
    })();

    return sub;
  }
}
