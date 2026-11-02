import { serve } from "@hono/node-server";
import { createApp, RecordingMessenger } from "./index.js";
import { LineApiClient } from "../../../packages/line/messaging-client.js";

const port = Number(process.env.PORT ?? "8787");
const channelSecret = process.env.LINE_CHANNEL_SECRET;
const accessToken = process.env.LINE_CHANNEL_ACCESS_TOKEN;
const missingVariables = [
  !channelSecret && "LINE_CHANNEL_SECRET",
  !accessToken && "LINE_CHANNEL_ACCESS_TOKEN",
].filter(Boolean);

if (missingVariables.length > 0) {
  console.warn(`[config] Missing runtime variables: ${missingVariables.join(", ")}. /health and Mini App remain available; real LINE replies are disabled.`);
}

const messenger = accessToken ? new LineApiClient(accessToken) : new RecordingMessenger();
const lineEnabled = Boolean(channelSecret && accessToken);

serve({ fetch: createApp({ channelSecret: channelSecret ?? "local-test-secret", messenger, lineEnabled }).app.fetch, port });
console.log(`LINE Portable Core gateway listening on http://localhost:${port}`);
