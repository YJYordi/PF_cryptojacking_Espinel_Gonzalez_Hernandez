import { IsInt, IsOptional, IsString } from 'class-validator';

export class CreateRuleDto {
  @IsString()
  vendor: 'suricata' | 'snort';

  @IsInt()
  sid: number;

  @IsString()
  name: string;

  @IsString()
  body: string;

  @IsOptional()
  tags?: string[];

  enabled?: boolean;  
}
