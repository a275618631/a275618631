import { describe, expect, it } from "vitest";
import { buildCardUrl, parseBusinessParams } from "../../apps/miniapp/src/liff.js";

describe("LIFF query handling", () => {
  it("round-trips ?, &, and % without manual concatenation", () => {
    const value = "a?b&c%20d";
    const url = buildCardUrl("https://example.com/card", { note: value });
    expect(parseBusinessParams(new URL(url).search).note).toBe(value);
  });
  it("parses ordinary query values", () => {
    expect(parseBusinessParams("?name=demo&count=2")).toEqual({ name: "demo", count: "2" });
  });
});
