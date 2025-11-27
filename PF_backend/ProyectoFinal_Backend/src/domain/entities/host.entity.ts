export class HostEntity {
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly createdAt: Date,
    public readonly lastSeen: Date,
    public readonly labels: any,
  ) {}
}
