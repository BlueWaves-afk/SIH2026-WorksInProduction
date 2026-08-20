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


/* ---------------------------------------------------------------------------
   Villager complaints.

   Per module_9 §5 these arrive as `InboundEvent` — a farmer raising their hand
   by missed call, IVR keypress or SMS reply — and open an M5 case. The shape is
   M9-owned and not yet in the shared contract set (module_0 §4), so it is typed
   locally here; it should be promoted to M1 before the contract freeze.
--------------------------------------------------------------------------- */

export type ComplaintIntent = "request_callback" | "report_damage" | "report_no_buyer" | "opt_out";
export type ComplaintChannel = "missed_call" | "ivr_keypress" | "sms_reply";

export interface VillagerComplaint {
  inbound_id: string;
  case_id: string;
  farmer_token: string;
  farmer_label: string;
  village: string;
  channel: ComplaintChannel;
  intent: ComplaintIntent;
  payload: string;
  received_at: string;
}

export const INTENT_LABEL: Record<ComplaintIntent, string> = {
  request_callback: "Callback requested",
  report_damage: "Crop damage",
  report_no_buyer: "No buyer",
  opt_out: "Opt-out",
};

export const CHANNEL_LABEL: Record<ComplaintChannel, string> = {
  missed_call: "Missed call",
  ivr_keypress: "IVR keypress",
  sms_reply: "SMS reply",
};

/** Fixed enum from module_5 §6.2 — no free-text-only close. */
export const RESOLUTION_LABEL: Record<string, string> = {
  SUPPORT_PROVIDED: "Support provided",
  REFERRED_EXTERNAL: "Referred to FPO/KVK",
  FARMER_UNREACHABLE: "Farmer unreachable",
  FALSE_POSITIVE: "No distress found",
  DUPLICATE: "Duplicate",
  NO_ACTION_NEEDED: "No action needed",
};

const hoursAgo = (h: number) => new Date(Date.parse(NOW) - h * 3600_000).toISOString();

export const demoComplaints: VillagerComplaint[] = [
  { inbound_id: "in-001", case_id: "case-001", farmer_token: "farmer-demo-token", farmer_label: "Farmer #A2F9", village: "Dindori", channel: "ivr_keypress", intent: "report_damage", payload: "Pressed 2 — crop damage in cotton plot", received_at: hoursAgo(3) },
  { inbound_id: "in-002", case_id: "case-002", farmer_token: "farmer-demo-token-2", farmer_label: "Farmer #B7K1", village: "Kalwan", channel: "missed_call", intent: "request_callback", payload: "Missed call to the district short code", received_at: hoursAgo(9) },
  { inbound_id: "in-003", case_id: "case-004", farmer_token: "farmer-demo-token-4", farmer_label: "Farmer #C3M8", village: "Dindori", channel: "sms_reply", intent: "report_no_buyer", payload: "SMS: \"no buyer for onion at mandi\"", received_at: hoursAgo(14) },
  { inbound_id: "in-004", case_id: "case-005", farmer_token: "farmer-demo-token-5", farmer_label: "Farmer #D8P2", village: "Peint", channel: "ivr_keypress", intent: "request_callback", payload: "Pressed 1 — wants an officer to call", received_at: hoursAgo(20) },
  { inbound_id: "in-005", case_id: "case-006", farmer_token: "farmer-demo-token-6", farmer_label: "Farmer #E4R7", village: "Kalwan", channel: "sms_reply", intent: "report_damage", payload: "SMS: \"leaves turning yellow after rain\"", received_at: hoursAgo(28) },
  { inbound_id: "in-006", case_id: "case-003", farmer_token: "farmer-demo-token-3", farmer_label: "Farmer #F1T5", village: "Peint", channel: "missed_call", intent: "request_callback", payload: "Missed call, callback completed", received_at: hoursAgo(40) },
];

/** Extra cases so the queue reflects a realistic district load. */
export const demoExtraCases: AlertCase[] = [
  { case_id: "case-004", event_id: "evt-demo-ps02-001", farmer_token: "farmer-demo-token-4", village_id: "Nashik / Dindori", recipient_role: "extension_officer", band: "amber", confidence: .78, assigned_to: "Officer Asha", channel_preferences: ["sms"], status: "new", sla_due_at: hoursAgo(-2) },
  { case_id: "case-005", event_id: "evt-demo-ps02-002", farmer_token: "farmer-demo-token-5", village_id: "Nashik / Peint", recipient_role: "extension_officer", band: "red", confidence: .82, assigned_to: "Officer Asha", channel_preferences: ["sms", "ivr"], status: "acknowledged", sla_due_at: hoursAgo(4) },
  { case_id: "case-006", event_id: "evt-demo-ps02-002", farmer_token: "farmer-demo-token-6", village_id: "Nashik / Kalwan", recipient_role: "extension_officer", band: "amber", confidence: .69, assigned_to: "Officer Vikram", channel_preferences: ["sms"], status: "visited", sla_due_at: hoursAgo(12) },
];
