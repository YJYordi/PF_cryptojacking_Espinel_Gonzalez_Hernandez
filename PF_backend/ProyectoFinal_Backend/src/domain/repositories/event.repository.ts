import { EventEntity } from '../entities/event.entity';
export abstract class EventRepository {
  abstract saveMany(events: EventEntity[]): Promise<void>;
  abstract findRecent(limit: number): Promise<EventEntity[]>;
}