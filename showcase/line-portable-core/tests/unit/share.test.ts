import { beforeEach, describe, expect, it, vi } from "vitest";
import liff from "@line/liff";
import { shareDemoCard } from "../../apps/miniapp/src/share.js";

vi.mock("@line/liff", () => ({
  default: {
    isApiAvailable: vi.fn(),
    shareTargetPicker: vi.fn(),
  },
}));

const mockedLiff = vi.mocked(liff);

describe("shareDemoCard", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('returns "shared" only for a success response', async () => {
    mockedLiff.isApiAvailable.mockReturnValue(true);
    mockedLiff.shareTargetPicker.mockResolvedValue({ status: "success" });

    await expect(shareDemoCard("https://example.com/card")).resolves.toBe("shared");
  });

  it("treats an undefined response as cancelled", async () => {
    mockedLiff.isApiAvailable.mockReturnValue(true);
    mockedLiff.shareTargetPicker.mockResolvedValue(undefined);

    await expect(shareDemoCard("https://example.com/card")).resolves.toBe("cancelled");
  });

  it("preserves unavailable behavior", async () => {
    mockedLiff.isApiAvailable.mockReturnValue(false);

    await expect(shareDemoCard("https://example.com/card")).resolves.toBe("unavailable");
    expect(mockedLiff.shareTargetPicker).not.toHaveBeenCalled();
  });

  it("treats cancellation errors as cancelled", async () => {
    mockedLiff.isApiAvailable.mockReturnValue(true);
    mockedLiff.shareTargetPicker.mockRejectedValue(new Error("user cancelled"));

    await expect(shareDemoCard("https://example.com/card")).resolves.toBe("cancelled");
  });
});
