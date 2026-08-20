import type { ActionCard, ConsentState, MandiQuote, RiskEvent } from "ui-kit";
import { demoActionCard, demoMandis, demoRiskEvent } from "../demo";
import { readCachedStatus, writeCachedStatus } from "../features/offline/statusCache";
import { accessToken, demoMode } from "../auth/supabase";

export interface FarmerProfileDraft {
  locale: "hi" | "mr" | "en";
  crop: string;
  season: string;
  irrigation: string;
  consent_flags: ConsentState;
}

interface StatusPayload {
  risk_event: RiskEvent;
  action_card: ActionCard;
  mandis: MandiQuote[];
}

/** Where the status on screen actually came from — surfaced to the farmer, never guessed. */
export type StatusSource = "api" | "cache" | "demo-fixture";

export interface FarmerStatus extends StatusPayload {
  cached_at: string;
  source: StatusSource;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
  const token = await accessToken();
  const response = await fetch(`${base}${path}`, { ...init, headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(init?.headers ?? {}) } });
  if (!response.ok) {
    const envelope = await response.json().catch(() => null) as { message?: string; request_id?: string } | null;
    const suffix = envelope?.request_id ? ` Reference: ${envelope.request_id}` : "";
    throw new Error(`${envelope?.message ?? `API request failed (${response.status})`}${suffix}`);
  }
  return response.json() as Promise<T>;
}

export async function submitFarmerProfile(draft: FarmerProfileDraft): Promise<{ farmer_token: string }> {
  const profile = await request<{ farmer_token: string }>("/api/v1/farmer-profiles", { method: "POST", body: JSON.stringify({
    village_id: "demo-village",
    crop: draft.crop,
    locale: draft.locale,
    sowing_date: new Date().toISOString().slice(0, 10),
    irrigation_type: draft.irrigation,
    area_band: "<1",
    consent_flags: {
      store_data: draft.consent_flags.storage,
      contact_me: draft.consent_flags.contact,
      use_analytics: draft.consent_flags.analytics,
      due_window: draft.consent_flags.due_window,
    },
  }) });
  window.localStorage.setItem("kisansetu.farmer_token", profile.farmer_token);
  return profile;
}

async function resolveFarmerToken(requested?: string): Promise<string> {
  if (requested) return requested;
  const stored = window.localStorage.getItem("kisansetu.farmer_token");
  if (stored) return stored;
  if (demoMode) return "farmer-demo";
  const profile = await request<{ farmer_token: string }>("/api/v1/farmer-profiles/me");
  window.localStorage.setItem("kisansetu.farmer_token", profile.farmer_token);
  return profile.farmer_token;
}

export async function loadFarmerStatus(farmerToken?: string): Promise<FarmerStatus> {
  try {
    const resolvedToken = await resolveFarmerToken(farmerToken);
    const [eventPage, marketPage] = await Promise.all([
      request<{ items: RiskEvent[] }>(`/api/v1/risk-events?farmer_token=${encodeURIComponent(resolvedToken)}`),
      request<{ items: MandiQuote[] }>(`/api/v1/mandis/compare?commodity=cotton&farmer_token=${encodeURIComponent(resolvedToken)}`),
    ]);
    const event = eventPage.items[0];
    if (!event) throw new Error("No risk event");
    const payload: StatusPayload = { risk_event: event, action_card: demoActionCard, mandis: marketPage.items.length ? marketPage.items : demoMode ? demoMandis : [] };
    const entry = writeCachedStatus(payload);
    return { ...payload, cached_at: entry.cached_at, source: "api" };
  } catch {
    // Offline or backend down: show the last status the farmer actually saw,
    // labelled with its age. Only fall back to fixtures on a first-ever run.
    const cached = readCachedStatus<StatusPayload>();
    if (cached) return { ...cached.payload, cached_at: cached.cached_at, source: "cache" };
    if (demoMode) return {
      risk_event: demoRiskEvent,
      action_card: demoActionCard,
      mandis: demoMandis,
      cached_at: new Date().toISOString(),
      source: "demo-fixture",
    };
    throw new Error("No saved status is available. Connect to the internet and try again.");
  }
}
