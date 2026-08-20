import type { AlertCase, CopilotBrief, Contributor, RiskEvent } from "ui-kit";

const NOW = "2026-08-20T06:00:00.000Z";

const driver = (signal: string, points: number, max_points: number, explanation: string, source: string): Contributor => ({ signal, points, max_points, explanation, source, observed_at: NOW });

export const demoEvents: RiskEvent[] = [
  {
    event_id: "evt-demo-ps02-001", farmer_token: "farmer-demo-token", village_id: "Nashik / Dindori", score: 74, band: "red", confidence: .86,
    contributors: [driver("rainfall_deficit", 20, 20, "Rainfall is 28% below the seasonal normal", "IMD rainfall feed"), driver("price_shock", 18, 20, "Cotton modal price is 17% below its seasonal baseline", "Agmarknet market feed"), driver("satellite_crop_stress", 11, 15, "Satellite crop signal shows growing vegetation stress", "Sentinel-2 crop observation")], action_ids: ["action-cotton-shock-1"], model_version: "fdi-v2", evaluated_at: NOW, expires_at: "2026-08-21T05:30:00.000Z", disclaimer: "This is not a credit, loan-default, or insurance score.", context_flags: ["price_feed_fresh"],
  },
  {
    event_id: "evt-demo-ps02-002", farmer_token: "farmer-demo-token-2", village_id: "Nashik / Kalwan", score: 58, band: "amber", confidence: .73,
    contributors: [driver("rainfall_deficit", 15, 20, "Rainfall is 19% below the seasonal normal", "IMD rainfall feed"), driver("price_shock", 12, 20, "Soybean price is below the three-year seasonal baseline", "Agmarknet market feed"), driver("irrigation_gap", 7, 10, "Rain-fed field has limited irrigation fallback", "Farmer profile")], action_ids: ["action-soybean-check-1"], model_version: "fdi-v2", evaluated_at: NOW, expires_at: "2026-08-21T05:30:00.000Z", disclaimer: "This is not a credit, loan-default, or insurance score.", context_flags: ["weather_feed_fresh"],
  },
  {
    event_id: "evt-demo-ps02-003", farmer_token: "farmer-demo-token-3", village_id: "Nashik / Peint", score: 31, band: "green", confidence: .91,
    contributors: [driver("rainfall_deficit", 8, 20, "Rainfall is close to the seasonal normal", "IMD rainfall feed"), driver("price_shock", 5, 20, "Market price is within the expected seasonal range", "Agmarknet market feed")], action_ids: [], model_version: "fdi-v2", evaluated_at: NOW, expires_at: "2026-08-21T05:30:00.000Z", disclaimer: "This is not a credit, loan-default, or insurance score.", context_flags: [],
  },
];

export const demoCases: AlertCase[] = [
  { case_id: "case-001", event_id: "evt-demo-ps02-001", farmer_token: "farmer-demo-token", village_id: "Nashik / Dindori", recipient_role: "extension_officer", band: "red", confidence: .86, assigned_to: "Officer Asha", channel_preferences: ["sms", "ivr"], status: "new", sla_due_at: "2026-08-20T10:00:00.000Z" },
  { case_id: "case-002", event_id: "evt-demo-ps02-002", farmer_token: "farmer-demo-token-2", village_id: "Nashik / Kalwan", recipient_role: "extension_officer", band: "amber", confidence: .73, assigned_to: "Officer Asha", channel_preferences: ["sms"], status: "acknowledged", sla_due_at: "2026-08-20T14:00:00.000Z" },
  { case_id: "case-003", event_id: "evt-demo-ps02-003", farmer_token: "farmer-demo-token-3", village_id: "Nashik / Peint", recipient_role: "extension_officer", band: "green", confidence: .91, assigned_to: "Officer Asha", channel_preferences: ["push"], status: "resolved", resolution_code: "no_action_needed" },
];

export const demoBrief: CopilotBrief = {
  case_id: "case-001",
  summary: "This farmer needs a same-day support check because rainfall deficit and below-baseline cotton price are reinforced by a satellite stress signal.",
  drivers: ["Rainfall is 28% below the seasonal normal", "Cotton modal price is 17% below its seasonal baseline", "Satellite crop signal shows growing vegetation stress"],
  scheme_matches: [{ scheme: "PMFBY", why: "The farmer may be eligible for crop-loss support; an officer will confirm.", verified: false, citations: [{ source_doc: "PMFBY operational guidelines", chunk_id: "pmfby-14", quote: "Coverage and claim decisions follow the applicable notified area and season." }] }],
  suggested_action: "REFER_KVK",
  draft_message: "Namaskar. We noticed a support signal for your cotton field. An agriculture officer will call to understand the situation and discuss available options. This is not a credit score.",
  citations: [{ source_doc: "PMFBY operational guidelines", chunk_id: "pmfby-14", quote: "Coverage and claim decisions follow the applicable notified area and season." }],
  model_version: "template-v1",
};
