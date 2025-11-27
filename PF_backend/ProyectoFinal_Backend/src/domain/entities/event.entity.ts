export class EventEntity {
  constructor(
    public readonly id: string,
    public readonly hostId: string,
    public readonly kind: string,
    public readonly ts: Date,
    public readonly payload: Record<string, unknown>,
  ) {}

  getSni(): string | undefined {
    return (this.payload as any)?.tls?.sni;
  }
}
