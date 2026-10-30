import { createApp, RecordingMessenger } from "../apps/gateway/src/index.js";
import { signLineBody } from "../packages/line/signature.js";

const secret = "smoke-secret";
const messenger = new RecordingMessenger();
const { app } = createApp({ channelSecret: secret, messenger });

const health = await app.request("http://localhost/health");
if (health.status !== 200) throw new Error(`/health returned ${health.status}`);
const card = await app.request("http://localhost/api/card/demo");
if (card.status !== 200 || !(await card.json()).messages) throw new Error("demo card smoke failed");
const calendar = await app.request("http://localhost/calendar/demo.ics");
if (calendar.status !== 200 || !calendar.headers.get("content-type")?.startsWith("text/calendar")) throw new Error("ICS smoke failed");
const invalid = await app.request("http://localhost/webhook/line", { method: "POST", headers: { "content-type": "application/json", "x-line-signature": "invalid" }, body: "{}" });
if (invalid.status !== 401) throw new Error(`invalid signature returned ${invalid.status}`);
const body = JSON.stringify({ events: [{ webhookEventId: "smoke-event", replyToken: "token", message: { type: "text", text: "/ping" } }] });
const signature = await signLineBody(body, secret);
const first = await app.request("http://localhost/webhook/line", { method: "POST", headers: { "content-type": "application/json", "x-line-signature": signature }, body });
const second = await app.request("http://localhost/webhook/line", { method: "POST", headers: { "content-type": "application/json", "x-line-signature": signature }, body });
if (first.status !== 200 || second.status !== 200 || messenger.replies.length !== 1) throw new Error("webhook dedupe smoke failed");
console.log("SMOKE PASS: /health, card, ICS, invalid signature, and webhook dedupe");
