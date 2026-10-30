import type { CardPayload, CardRepository } from "../../packages/core/ports.js";

export const demoCard: CardPayload = {
  messages: [
    {
      type: "flex",
      altText: "Demo booking card",
      contents: {
        type: "bubble",
        size: "kilo",
        body: {
          type: "box",
          layout: "vertical",
          contents: [
            { type: "text", text: "Portable Core Demo", weight: "bold", size: "lg" },
            { type: "text", text: "Share this card from LINE MINI App.", wrap: true, margin: "md" },
          ],
        },
        footer: {
          type: "box",
          layout: "vertical",
          contents: [
            {
              type: "button",
              style: "primary",
              action: { type: "uri", label: "Open calendar", uri: "https://calendar.google.com/calendar/u/0/r/eventedit" },
            },
          ],
        },
      },
    },
  ],
};

export class MemoryCardRepository implements CardRepository {
  async getByToken(token: string): Promise<CardPayload | null> {
    return token === "demo" ? demoCard : null;
  }
}
