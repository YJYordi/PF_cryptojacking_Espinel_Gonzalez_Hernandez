import { IsArray, IsObject, IsString } from 'class-validator';

export class IngestEveDto {
  @IsString() host_id!: string;
  @IsArray() events!: Record<string, unknown>[];
}
