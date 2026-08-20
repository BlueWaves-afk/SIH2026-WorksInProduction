/**
 * Typed HTTP view models used by the two M8 apps.
 *
 * M1 remains the owner of the canonical Python contracts. These TypeScript
 * shapes deliberately mirror the wire format so the eventual OpenAPI client
 * can replace the demo client without changing presentation components.
 */
export type Band = "green" | "amber" | "red";

export type CaseStatus = "new" | "acknowledged" | "visited" | "referred" | "resolved";

export interface Contributor {
  signal: string;
  points: number;
  max_points: number;
  explanation: string;
  source: string;
  observed_at: string;
}

export interface RiskEvent {
  event_id: string;
  farmer_token: string;
  village_id: string;
  score: number;
  band: Band;
  confidence: number;
  contributors: Contributor[];
  action_ids: string[];
  model_version: string;
  evaluated_at?: string;
  expires_at: string;
  disclaimer: string;
  context_flags: string[];
}

export interface ActionStep {
  text: string;
  audio_key?: string;
  deep_link?: string;
}

export interface ActionCard {
  card_id: string;
  locale: string;
  title: string;
  steps: ActionStep[];
  scheme_refs: string[];
  approved_by: string;
  version: string;
  source_refs: string[];
}

export interface AlertCase {
  case_id: string;
  event_id: string;
  farmer_token: string;
  village_id: string;
  recipient_role: string;
  band: Band;
  confidence: number;
  assigned_to?: string;
  channel_preferences: string[];
  status: CaseStatus;
  sent_at?: string;
  ack_at?: string;
  sla_due_at?: string;
  resolution_code?: string;
  notes?: string;
}

export interface Citation {
  source_doc: string;
  chunk_id: string;
  quote: string;
}

export interface SchemeMatch {
  scheme: string;
  why: string;
  citations: Citation[];
  verified: boolean;
}

export interface CopilotBrief {
  case_id: string;
  summary: string;
  drivers: string[];
  scheme_matches: SchemeMatch[];
  suggested_action?: string;
  draft_message?: string;
  citations: Citation[];
  model_version?: string;
}

export interface MandiQuote {
  mandi: string;
  distance_km: number;
  modal_price: number;
  change_pct: number;
  verified_at: string;
}

export interface ConsentState {
  storage: boolean;
  contact: boolean;
  analytics: boolean;
  due_window: boolean;
}

export const BAND_LABELS: Record<Band, string> = {
  green: "Stable",
  amber: "Needs attention",
  red: "Support needed",
};

export const BAND_ORDER: Record<Band, number> = { red: 0, amber: 1, green: 2 };
