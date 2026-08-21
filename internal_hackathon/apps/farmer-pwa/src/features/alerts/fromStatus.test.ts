import { describe, expect, it } from "vitest";
import type { FarmerStatus } from "../../api/client";
import { buildAlerts } from "./fromStatus";

function status(risk: Partial<FarmerStatus["risk_event"]>): FarmerStatus {
  return {
    risk_event: {
      event_id: "evt-1",
      farmer_token: "farmer-1",
      village_id: "demo-village",
      score: 74,
      band: "red",
      confidence: 0.8,
      contributors: [],
      action_ids: [],
      model_version: "fdi-v2",
      expires_at: "2026-08-22T00:00:00Z",
      disclaimer: "This is not a credit, loan-default, or insurance score.",
      context_flags: [],
      ...risk,
    },
  } as FarmerStatus;
}

describe("buildAlerts", () => {
  it("returns an empty feed when there is no status", () => {
    expect(buildAlerts(null)).toEqual([]);
  });

  it("maps real contributors to alert tiles, most-severe first", () => {
    const alerts = buildAlerts(
      status({
        contributors: [
          { signal: "rainfall_deficit", points: 20, max_points: 20, explanation: "", source: "IMD", observed_at: "" },
          { signal: "price_shock", points: 8, max_points: 20, explanation: "", source: "Agmarknet", observed_at: "" },
          { signal: "repayment_window", points: 0, max_points: 20, explanation: "", source: "Farmer", observed_at: "" },
        ],
      }),
    );
    // Zero-point drivers are dropped; the rest are sorted by points desc.
    expect(alerts.map((a) => a.id)).toEqual(["evt-1-rainfall_deficit", "evt-1-price_shock"]);
    expect(alerts[0].kind).toBe("rain");
    expect(alerts[0].band).toBe("red"); // 20/20 -> red
    expect(alerts[0].meta).toBe("demo-village · 74/100");
    expect(alerts[1].kind).toBe("market");
    expect(alerts[1].band).toBe("amber"); // 8/20 = 0.4 -> amber
  });

  it("shows a single all-clear tile when no driver is active", () => {
    const alerts = buildAlerts(status({ band: "green", score: 12, contributors: [] }));
    expect(alerts).toHaveLength(1);
    expect(alerts[0].band).toBe("green");
    expect(alerts[0].meta).toBe("demo-village · 12/100");
  });

  it("only ever emits the four supported alert kinds", () => {
    const alerts = buildAlerts(
      status({
        contributors: [
          { signal: "some_unknown_signal", points: 5, max_points: 10, explanation: "", source: "x", observed_at: "" },
        ],
      }),
    );
    expect(["crop", "rain", "market", "pest"]).toContain(alerts[0].kind);
  });
});
