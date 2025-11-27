import { AlertEntity } from '../entities/alert.entity';

export abstract class AlertRepository {
  abstract create(alert: AlertEntity): Promise<AlertEntity>;
  abstract findByEvent(eventId: string): Promise<AlertEntity[]>;
  abstract findRecent(limit?: number): Promise<AlertEntity[]>;
}
