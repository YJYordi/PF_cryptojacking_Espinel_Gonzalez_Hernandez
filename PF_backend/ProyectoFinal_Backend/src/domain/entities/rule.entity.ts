export class RuleEntity {
  constructor(
    public readonly id: string,
    public readonly type: string,
    public readonly pattern: string,
    public readonly description: string | null,
    public readonly enabled: boolean,
    public readonly tags: string[],

    public readonly vendor?: string | null,
    public readonly sid?: number | null,
    public readonly name?: string | null,
    public readonly body?: string | null,
  ) {}
}
