import { describe, expect, it } from "vitest";
import { demoIcs, googleCalendarUrl } from "../../packages/calendar/index.js";
import { validateFlexMessages } from "../../packages/line/flex-validator.js";

describe("Flex validator and Calendar", () => {
  it("accepts demo Flex and rejects empty text / invalid URI", async () => {
    const valid = { type: "flex", altText: "Demo", contents: { type: "bubble", body: { type: "box", contents: [{ type: "text", text: "ok" }] } } };
    expect(validateFlexMessages([valid]).valid).toBe(true);
    expect(validateFlexMessages([{ type: "flex", altText: "", contents: {} }]).valid).toBe(false);
    expect(validateFlexMessages([{ type: "text", text: "ok", action: { type: "uri", uri: "http://insecure" } }]).valid).toBe(false);
  });
  it("produces encoded Google Calendar URL and ICS", () => {
    const url = googleCalendarUrl({ title: "A&B", start: "20260924T010000Z", end: "20260924T020000Z" });
    expect(url).toContain("A%26B");
    expect(demoIcs()).toContain("BEGIN:VCALENDAR");
  });
});
