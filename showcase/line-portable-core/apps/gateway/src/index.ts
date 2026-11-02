import { Hono } from "hono";
import { serveStatic } from "@hono/node-server/serve-static";
import { MemoryStore } from "../../../adapters/memory/memory-store.js";
import { MemoryCardRepository } from "../../../adapters/memory/card-repository.js";
import type { LineMessenger } from "../../../packages/core/ports.js";
import { createCardRoute } from "./routes/card.js";
import { createLineWebhookRoute } from "./routes/line-webhook.js";
import { demoIcs, googleCalendarUrl } from "../../../packages/calendar/index.js";

export class RecordingMessenger implements LineMessenger {
  readonly replies: Array<{ replyToken: string; messages: unknown[] }> = [];
  readonly pushes: Array<{ to: string; messages: unknown[] }> = [];
  async reply(replyToken: string, messages: unknown[]): Promise<void> {
    this.replies.push({ replyToken, messages });
  }
  async push(to: string, messages: unknown[]): Promise<void> {
    this.pushes.push({ to, messages });
  }
}

export function createApp({
  channelSecret = "local-test-secret",
  store = new MemoryStore(),
  messenger = new RecordingMessenger(),
  lineEnabled = true,
}: {
  channelSecret?: string;
  store?: MemoryStore;
  messenger?: LineMessenger;
  lineEnabled?: boolean;
} = {}) {
  const app = new Hono();
  app.get("/health", (context) => context.json({ ok: true }));
  app.route("/api/card", createCardRoute(new MemoryCardRepository()));
  app.route("/webhook/line", createLineWebhookRoute(store, messenger, channelSecret, lineEnabled));
  app.get("/calendar/demo.ics", (context) => new Response(demoIcs(), { headers: { "Content-Type": "text/calendar; charset=utf-8" } }));
  app.get("/calendar/demo", (context) => context.redirect(googleCalendarUrl({
    title: "LINE Portable Core Demo",
    start: "20260924T010000Z",
    end: "20260924T020000Z",
    details: "Created by LINE Portable Core MVP",
  })));
  app.use("/*", serveStatic({ root: "./dist/miniapp" }));
  return { app, messenger };
}

export const app = createApp().app;
