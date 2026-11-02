import { Hono } from "hono";
import type { IdempotencyStore, LineMessenger } from "../../../../packages/core/ports.js";
import { handleLineWebhook } from "../../../../packages/line/webhook.js";

export function createLineWebhookRoute(store: IdempotencyStore, messenger: LineMessenger, channelSecret: string, enabled = true) {
  const app = new Hono();
  app.post("/", async (context) => {
    console.info("[line-webhook] request arrived route=/webhook/line");
    if (!enabled) {
      console.warn("[line-webhook] unavailable missing=LINE_CHANNEL_SECRET,LINE_CHANNEL_ACCESS_TOKEN");
      return context.json({ status: 503, processed: 0, duplicate: 0 }, 503);
    }
    const rawBody = await context.req.text();
    const result = await handleLineWebhook({
      rawBody,
      signature: context.req.header("x-line-signature") ?? null,
      channelSecret,
      store,
      messenger,
      logger: (event, details = {}) => console.info(`[line-webhook] ${event}`, details),
    });
    return context.json(result, result.status as 200 | 400 | 401);
  });
  return app;
}
