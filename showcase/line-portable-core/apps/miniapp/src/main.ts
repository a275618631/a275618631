import liff from "@line/liff";
import { parseBusinessParams, buildCardUrl } from "./liff.js";
import { shareDemoCard } from "./share.js";

const status = document.querySelector<HTMLParagraphElement>("#status");
const button = document.querySelector<HTMLButtonElement>("#share");
const liffId = import.meta.env.VITE_LINE_LIFF_ID;

async function main(): Promise<void> {
  if (!liffId) throw new Error("VITE_LINE_LIFF_ID is not configured");
  await liff.init({ liffId });
  console.info("[miniapp] liff.init success");
  const params = parseBusinessParams(window.location.search);
  const cardUrl = buildCardUrl(`${window.location.origin}/api/card/demo`, params);
  button?.addEventListener("click", async () => {
    if (status) status.textContent = "Sharing…";
    console.info("[miniapp] shareTargetPicker invoked");
    try {
      const result = await shareDemoCard(cardUrl);
      console.info(`[miniapp] shareTargetPicker ${result}`);
      if (status) status.textContent = result === "unavailable" ? "This device cannot open the share picker." : result === "cancelled" ? "Share cancelled." : "Card shared.";
    } catch (error) {
      console.error("[miniapp] LINE API error", error instanceof Error ? error.name : "UnknownError");
      if (status) status.textContent = "The LINE action failed. Check the browser console diagnostic code.";
    }
  });
  if (status) status.textContent = "Ready to share the demo card.";
}

void main().catch((error: unknown) => {
  console.error("[miniapp] liff.init failure", error instanceof Error ? error.name : "UnknownError");
  if (status) status.textContent = error instanceof Error && error.message === "VITE_LINE_LIFF_ID is not configured"
    ? error.message
    : "Mini App failed to initialize. Check the browser console diagnostic code.";
});
