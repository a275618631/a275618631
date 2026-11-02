import type { LineMessenger } from "../core/ports.js";

export class LineApiClient implements LineMessenger {
  constructor(
    private readonly accessToken: string,
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  private async post(path: string, body: unknown): Promise<void> {
    const response = await this.fetchImpl(`https://api.line.me/v2/bot/message/${path}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${this.accessToken}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`LINE API ${path} failed with ${response.status}`);
  }

  reply(replyToken: string, messages: unknown[]): Promise<void> {
    return this.post("reply", { replyToken, messages });
  }

  push(to: string, messages: unknown[]): Promise<void> {
    return this.post("push", { to, messages });
  }
}
