import { describe, expect, it } from "vitest";
import fixture from "../fixtures/line-webhook.json" with { type: "json" };
import { MemoryStore } from "../../adapters/memory/memory-store.js";
import { RecordingMessenger } from "../../apps/gateway/src/index.js";
import { handleLineWebhook } from "../../packages/line/webhook.js";
import { signLineBody, verifyLineSignature } from "../../packages/line/signature.js";

const rawFixture = JSON.stringify(fixture);
const secret = "test-secret";

describe("LINE webhook security", () => {
  it("accepts a valid signature fixture", async () => {
    const signature = await signLineBody(rawFixture, secret);
    expect(await verifyLineSignature(rawFixture, signature, secret)).toBe(true);
  });

  it("rejects an invalid signature before processing", async () => {
    const messenger = new RecordingMessenger();
    const result = await handleLineWebhook({ rawBody: rawFixture, signature: "invalid", channelSecret: secret, store: new MemoryStore(), messenger });
    expect(result.status).toBe(401);
    expect(messenger.replies).toHaveLength(0);
  });

  it("deduplicates webhookEventId and replies /ping once", async () => {
    const messenger = new RecordingMessenger();
    const store = new MemoryStore();
    const signature = await signLineBody(rawFixture, secret);
    const first = await handleLineWebhook({ rawBody: rawFixture, signature, channelSecret: secret, store, messenger });
    const second = await handleLineWebhook({ rawBody: rawFixture, signature, channelSecret: secret, store, messenger });
    expect(first.processed).toBe(1);
    expect(second.duplicate).toBe(1);
    expect(messenger.replies).toEqual([{ replyToken: "reply-token-demo", messages: [{ type: "text", text: "pong" }] }]);
  });

  it("does not mark a failed /ping reply and processes its redelivery", async () => {
    const store = new MemoryStore();
    class FailOnceMessenger extends RecordingMessenger {
      attempts = 0;

      override async reply(replyToken: string, messages: unknown[]): Promise<void> {
        this.attempts += 1;
        if (this.attempts === 1) throw new Error("temporary reply failure");
        await super.reply(replyToken, messages);
      }
    }
    const messenger = new FailOnceMessenger();
    const signature = await signLineBody(rawFixture, secret);

    await expect(handleLineWebhook({ rawBody: rawFixture, signature, channelSecret: secret, store, messenger })).rejects.toThrow("temporary reply failure");
    expect(await store.seen("01HDEMO000000000000000001")).toBe(false);

    const redelivery = await handleLineWebhook({ rawBody: rawFixture, signature, channelSecret: secret, store, messenger });
    const duplicate = await handleLineWebhook({ rawBody: rawFixture, signature, channelSecret: secret, store, messenger });

    expect(redelivery.processed).toBe(1);
    expect(duplicate.duplicate).toBe(1);
    expect(messenger.attempts).toBe(2);
    expect(messenger.replies).toHaveLength(1);
  });
});
