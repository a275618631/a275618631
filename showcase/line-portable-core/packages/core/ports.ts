export interface CardPayload {
  messages: unknown[];
}

export interface IdempotencyStore {
  seen(eventId: string): Promise<boolean>;
  mark(eventId: string, ttlSeconds?: number): Promise<void>;
}

export interface LineMessenger {
  reply(replyToken: string, messages: unknown[]): Promise<void>;
  push(to: string, messages: unknown[]): Promise<void>;
  getMonthlyUsage?(): Promise<{ used: number; limit?: number }>;
}

export interface CardRepository {
  getByToken(token: string): Promise<CardPayload | null>;
}

export interface BookingService {
  getAvailability(input: unknown): Promise<unknown>;
  createBooking(input: unknown): Promise<unknown>;
  getBooking(id: string): Promise<unknown>;
  cancelBooking(id: string): Promise<unknown>;
  rescheduleBooking(id: string, input: unknown): Promise<unknown>;
}

export interface ProductionQueryService {
  queryProduction(input: unknown): Promise<unknown>;
  queryIncidents(input: unknown): Promise<unknown>;
}
