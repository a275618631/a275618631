import liff from "@line/liff";

export async function shareDemoCard(cardUrl: string): Promise<"shared" | "cancelled" | "unavailable"> {
  if (!liff.isApiAvailable("shareTargetPicker")) return "unavailable";
  try {
    const result = await liff.shareTargetPicker([
      {
        type: "flex",
        altText: "Portable Core Demo",
        contents: {
          type: "bubble",
          body: { type: "box", layout: "vertical", contents: [{ type: "text", text: "LINE Portable Core Demo" }] },
          footer: { type: "box", layout: "vertical", contents: [{ type: "button", action: { type: "uri", label: "Open card", uri: cardUrl } }] },
        },
      },
    ]);
    return result?.status === "success" ? "shared" : "cancelled";
  } catch (error) {
    if (error instanceof Error && /cancel/i.test(error.message)) return "cancelled";
    throw error;
  }
}
