import type { FarmerStatus } from "../../api/client";
import type { DemoAlert } from "../../demo";

/**
 * Derive the farmer alerts feed from the *real* scored risk event.
 *
 * Each card is one active FDI driver of the farmer's current risk, so the
 * alerts screen reflects live scoring instead of static demo tiles. Only the
 * four AlertKind values are emitted so the design system and the
 * `alerts.kind.*` i18n keys stay in sync.
 */
const SIGNAL_META: Record<string, { kind: DemoAlert["kind"]; title: string }> = {
  rainfall_deficit: { kind: "rain", title: "Rainfall\nDeficit" },
  rainfall_excess: { kind: "rain", title: "Heavy Rain\nWarning" },
  flood_risk: { kind: "rain", title: "Flood\nRisk" },
  satellite_crop_stress: { kind: "crop", title: "Crop Stress\nAlert" },
  pest_pressure: { kind: "pest", title: "Pest\nWatch" },
  price_shock: { kind: "market", title: "Market Price\nDrop" },
  repayment_window: { kind: "crop", title: "Repayment\nWindow" },
  acute_farmer_report: { kind: "crop", title: "Reported\nDamage" },
};

function titleFromSignal(signal: string): string {
  const words = signal.split("_").map((word) => word.charAt(0).toUpperCase() + word.slice(1));
  const mid = Math.ceil(words.length / 2);
  return `${words.slice(0, mid).join(" ")}\n${words.slice(mid).join(" ")}`.trim();
}

/** A single driver's own severity, so an amber overall event can still surface
 * a red driver card — the tile reflects the signal, not just the headline band. */
function contributorBand(points: number, maxPoints: number): DemoAlert["band"] {
  const ratio = maxPoints > 0 ? points / maxPoints : 0;
  if (ratio >= 0.7) return "red";
  if (ratio >= 0.4) return "amber";
  return "green";
}

export function buildAlerts(status: FarmerStatus | null): DemoAlert[] {
  const event = status?.risk_event;
  if (!event) return [];

  const contributors = [...(event.contributors ?? [])]
    .filter((item) => item.points > 0)
    .sort((a, b) => b.points - a.points)
    .slice(0, 4);

  if (contributors.length === 0) {
    // No active drivers: one honest "all clear" tile beats an empty grid.
    return [
      {
        id: `status-${event.event_id}`,
        title: "No Urgent\nAlerts",
        kind: "crop",
        meta: `${event.village_id} · ${Math.round(event.score)}/100`,
        band: "green",
        span: "tall",
      },
    ];
  }

  return contributors.map((item, index) => {
    const meta = SIGNAL_META[item.signal];
    return {
      id: `${event.event_id}-${item.signal}`,
      title: meta?.title ?? titleFromSignal(item.signal),
      kind: meta?.kind ?? "crop",
      meta:
        index === 0
          ? `${event.village_id} · ${Math.round(event.score)}/100`
          : `${Math.round(item.points)}/${Math.round(item.max_points)} pts`,
      band: contributorBand(item.points, item.max_points),
      span: index % 3 === 0 ? "tall" : "short",
    };
  });
}
