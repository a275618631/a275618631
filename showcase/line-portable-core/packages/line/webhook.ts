import type { IdempotencyStore, LineMessenger } from "../core/ports.js";
import { verifyLineSignature } from "./signature.js";

export interface LineWebhookEvent {
  webhookEventId?: string;
  replyToken?: string;
  type?: string;
  message?: { type?: string; text?: string };
}

export interface LineWebhookBody {
  events?: LineWebhookEvent[];
}

export type WebhookLogEvent =
  | "signature_valid"
  | "signature_invalid"
  | "event_received"
  | "command_ping"
  | "reply_attempted"
  | "reply_success"
  | "reply_failure";

export type WebhookLogger = (event: WebhookLogEvent, details?: Record<string, string>) => void;

export async function handleLineWebhook({
  rawBody,
  signature,
  channelSecret,
  store,
  messenger,
  logger = () => undefined,
}: {
  rawBody: string;
  signature: string | null;
  channelSecret: string;
  store: IdempotencyStore;
  messenger: LineMessenger;
  logger?: WebhookLogger;
}): Promise<{ status: number; processed: number; duplicate: number }> {
  if (!(await verifyLineSignature(rawBody, signature, channelSecret))) {
    logger("signature_invalid");
    return { status: 401, processed: 0, duplicate: 0 };
  }
  logger("signature_valid");

  let body: LineWebhookBody;
  try {
    body = JSON.parse(rawBody) as LineWebhookBody;
  } catch {
    return { status: 400, processed: 0, duplicate: 0 };
  }
  if (!Array.isArray(body.events)) return { status: 400, processed: 0, duplicate: 0 };

  let processed = 0;
  let duplicate = 0;
  for (const event of body.events) {
    if (!event.webhookEventId) continue;
    logger("event_received", {
      webhookEventId: event.webhookEventId,
      eventType: event.type ?? "unknown",
    });
    if (await store.seen(event.webhookEventId)) {
      duplicate += 1;
      continue;
    }
    if (event.message?.type === "text" && event.message.text?.trim() === "/ping" && event.replyToken) {
      logger("command_ping", { webhookEventId: event.webhookEventId });
      logger("reply_attempted", { webhookEventId: event.webhookEventId });
      try {
        await messenger.reply(event.replyToken, [{ type: "text", text: "pong" }]);
        logger("reply_success", { webhookEventId: event.webhookEventId });
      } catch (error) {
        logger("reply_failure", {
          webhookEventId: event.webhookEventId,
          errorType: error instanceof Error ? error.name : "UnknownError",
        });
        throw error;
      }
    }
    await store.mark(event.webhookEventId);
    processed += 1;
  }
  return { status: 200, processed, duplicate };
}
