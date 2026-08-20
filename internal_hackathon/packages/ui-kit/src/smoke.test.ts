import { describe, expect, it } from "vitest";
import { BAND_LABELS, BAND_ORDER } from "./types";

describe("ui-kit primitives", () => {
  it("uses the shared traffic-light order and labels", () => {
    expect(BAND_ORDER.red).toBeLessThan(BAND_ORDER.amber);
    expect(BAND_ORDER.amber).toBeLessThan(BAND_ORDER.green);
    expect(BAND_LABELS.red).toBe("Support needed");
  });
});
