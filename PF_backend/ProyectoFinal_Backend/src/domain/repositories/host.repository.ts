import { HostEntity } from '../entities/host.entity';

export abstract class HostRepository {
  abstract findById(id: string): Promise<HostEntity | null>;
  abstract upsert(id: string, name?: string): Promise<HostEntity>;
  abstract list(): Promise<HostEntity[]>;
}
