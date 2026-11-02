import { Hono } from "hono";
import type { CardRepository } from "../../../../packages/core/ports.js";
import { validateFlexMessages } from "../../../../packages/line/flex-validator.js";

export function createCardRoute(repository: CardRepository) {
  const app = new Hono();
  app.get("/demo", async (context) => {
    const card = await repository.getByToken("demo");
    if (!card) return context.json({ error: "card_not_found" }, 404);
    const validation = validateFlexMessages(card.messages);
    if (!validation.valid) return context.json({ error: "invalid_card", details: validation.errors }, 500);
    return context.json(card);
  });
  return app;
}
