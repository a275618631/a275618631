import { describe, expect, it } from "vitest";
import { canPush, estimateMonthlyRecipients } from "../../packages/core/quota-policy.js";

describe("QuotaGuard", () => {
  it("estimates recipient count, not request count", () => {
    expect(estimateMonthlyRecipients({ recipientsPerSend: 4, sendsPerMonth: 3 })).toBe(12);
  });
  it.each([[159, true], [160, true], [161, false]] as const)("checks budget boundary %i", (used, expected) => {
    expect(canPush({ usedThisMonth: used, plannedRecipients: 0 })).toBe(expected);
  });
});
