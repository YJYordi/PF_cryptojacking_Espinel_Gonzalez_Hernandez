// Tipos compartidos para la API
export interface Rule {
  id: string;
  type: string;
  pattern: string;
  description?: string | null;
  enabled: boolean;
  tags: string[];
  createdAt: string;
  vendor?: string | null;
  sid?: number | null;
  name?: string | null;
  body?: string | null;
}

export interface CreateRuleDto {
  vendor: 'suricata' | 'snort';
  sid: number;
  name: string;
  body: string;
  tags?: string[];
  enabled?: boolean;
}

export interface Alert {
  id: string;
  eventId: string;
  severity: string;
  reason: any;
  createdAt: string;
  event?: {
    id: string;
    hostId: string;
    kind: string;
    payload: any;
    ts: string;
  };
}

export interface IngestEveDto {
  host_id: string;
  events: Array<Record<string, unknown>>;
}

