export class AlertEntity {
  constructor(
    public readonly id: string,
    public readonly eventId: string,
    public readonly severity: 'low' | 'med' | 'high',
    public readonly reason: any,
    public readonly createdAt: Date,
  ) {}
}
