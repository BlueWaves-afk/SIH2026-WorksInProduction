import { describe, expect, it } from "vitest";
import { demoActionCard, demoRiskEvent } from "./demo";

describe("farmer PWA first vertical slice", () => {
  it("renders a fixture with the shared upstream explanation shape", () => {
    expect(demoRiskEvent.band).toBe("red");
    expect(demoRiskEvent.contributors).toHaveLength(4);
    expect(demoRiskEvent.disclaimer).toContain("not a credit");
    expect(demoActionCard.steps.length).toBeGreaterThan(1);
  });
});
