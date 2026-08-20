import type { ActionCard, MandiQuote, RiskEvent } from "ui-kit";

const OBSERVED_AT = "2026-08-20T05:30:00.000Z";

export const demoRiskEvent: RiskEvent = {
  event_id: "evt-demo-ps02-001",
  farmer_token: "farmer-demo-token",
  village_id: "Nashik / Dindori",
  score: 74,
  band: "red",
  confidence: 0.86,
  contributors: [
    { signal: "rainfall_deficit", points: 20, max_points: 20, explanation: "Rainfall is 28% below the seasonal normal", source: "IMD rainfall feed", observed_at: OBSERVED_AT },
    { signal: "price_shock", points: 18, max_points: 20, explanation: "Cotton modal price is 17% below its seasonal baseline", source: "Agmarknet market feed", observed_at: OBSERVED_AT },
    { signal: "satellite_crop_stress", points: 11, max_points: 15, explanation: "Satellite crop signal shows growing vegetation stress", source: "Sentinel-2 crop observation", observed_at: OBSERVED_AT },
    { signal: "repayment_window", points: 9, max_points: 20, explanation: "An opted-in repayment window is approaching", source: "Farmer-provided window", observed_at: OBSERVED_AT },
  ],
  action_ids: ["action-cotton-shock-1"],
  model_version: "fdi-v2",
  evaluated_at: OBSERVED_AT,
  expires_at: "2026-08-21T05:30:00.000Z",
  disclaimer: "This is not a credit, loan-default, or insurance score.",
  context_flags: ["price_feed_fresh", "weather_feed_fresh"],
};

export const demoActionCard: ActionCard = {
  card_id: "action-cotton-shock-1",
  locale: "mr",
  title: "आजची सुरक्षित पुढची पावले",
  steps: [
    { text: "पुढील 48 तासांत पाण्याची उपलब्धता आणि पिकाची स्थिती स्थानिक कृषी अधिकाऱ्याला कळवा." },
    { text: "दोन जवळच्या बाजारांचे दर तपासा; जबरदस्तीने विक्री करण्यापूर्वी FPO कडून पर्याय विचारा.", deep_link: "mandi-compare" },
    { text: "अधिकारी किंवा हेल्पलाइनकडून संपर्काची विनंती करा; हा संदेश सल्ला आहे, कर्जाचा निर्णय नाही." },
  ],
  scheme_refs: ["PMFBY", "KCC"],
  approved_by: "District agronomy review board",
  version: "2",
  source_refs: ["IMD rainfall feed", "Agmarknet market feed", "approved action library"],
};

export const demoMandis: MandiQuote[] = [
  { mandi: "Dindori", distance_km: 8, modal_price: 6120, change_pct: -17, verified_at: OBSERVED_AT },
  { mandi: "Lasalgaon", distance_km: 31, modal_price: 6480, change_pct: -11, verified_at: OBSERVED_AT },
  { mandi: "Nashik", distance_km: 42, modal_price: 6550, change_pct: -9, verified_at: OBSERVED_AT },
];

export type AlertKind = "crop" | "rain" | "market" | "pest";

export interface DemoAlert {
  id: string;
  title: string;
  kind: AlertKind;
  meta: string;
  band: "red" | "amber" | "green";
  span: "tall" | "short";
}

/** Alerts the farmer can choose from before opening a specific timeline. */
export const demoAlerts: DemoAlert[] = [
  { id: "cotton-stress", title: "Cotton Stress\nAlert", kind: "crop", meta: "Dindori · 74/100", band: "red", span: "tall" },
  { id: "heavy-rain", title: "Heavy Rain\nWarning", kind: "rain", meta: "Nashik · next 48h", band: "amber", span: "short" },
  { id: "market-drop", title: "Market Price\nDrop", kind: "market", meta: "Cotton · −17%", band: "amber", span: "short" },
  { id: "pest-watch", title: "Pink Bollworm\nWatch", kind: "pest", meta: "3 villages nearby", band: "green", span: "tall" },
];
