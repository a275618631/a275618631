import type { IdempotencyStore } from "../../packages/core/ports.js";

export class MemoryStore implements IdempotencyStore {
  private readonly values = new Map<string, number>();

  async seen(eventId: string): Promise<boolean> {
    const expiresAt = this.values.get(eventId);
    if (expiresAt === undefined) return false;
    if (expiresAt <= Date.now()) {
      this.values.delete(eventId);
      return false;
    }
    return true;
  }

  async mark(eventId: string, ttlSeconds = 86_400): Promise<void> {
    this.values.set(eventId, Date.now() + ttlSeconds * 1000);
  }
}
