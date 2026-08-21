import type { ActionCard, ConsentState, CopilotMessage, MandiQuote, RiskEvent } from "ui-kit";
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
  const response = await requestResponse(path, init);
  return response.json() as Promise<T>;
}

async function requestResponse(path: string, init?: RequestInit): Promise<Response> {
  const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
  const token = await accessToken();
  const response = await fetch(`${base}${path}`, { ...init, headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(init?.headers ?? {}) } });
  if (!response.ok) {
    const envelope = await response.json().catch(() => null) as { message?: string; request_id?: string } | null;
    const suffix = envelope?.request_id ? ` Reference: ${envelope.request_id}` : "";
    throw new Error(`${envelope?.message ?? `API request failed (${response.status})`}${suffix}`);
  }
  return response;
}

export async function submitFarmerProfile(draft: FarmerProfileDraft): Promise<{ farmer_token: string }> {
  let profile: { farmer_token: string };
  try {
    profile = await request<{ farmer_token: string }>("/api/v1/farmer-profiles", { method: "POST", body: JSON.stringify({
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
  } catch (error) {
    // Older backend deployments returned 409 for an existing authenticated
    // profile. Recover by signing in to that profile instead of making the
    // farmer repeat setup or showing a raw conflict error.
    const message = error instanceof Error ? error.message.toLowerCase() : "";
    if (!message.includes("already has a profile") && !message.includes("profile already exists")) throw error;
    profile = await request<{ farmer_token: string }>("/api/v1/farmer-profiles/me");
  }
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
    const [initialEventPage, marketPage] = await Promise.all([
      request<{ items: RiskEvent[] }>(`/api/v1/risk-events?farmer_token=${encodeURIComponent(resolvedToken)}`),
      request<{ items: MandiQuote[] }>(`/api/v1/mandis/compare?commodity=cotton&farmer_token=${encodeURIComponent(resolvedToken)}`),
    ]);
    // Profiles created before the status-bootstrap release may have no event
    // row yet. Ask the authenticated backend to create one from currently
    // stored observations; this is not a fixture or a client-side score.
    const event = initialEventPage.items[0] ?? await request<RiskEvent>('/api/v1/risk-events/recalculate', {
      method: 'POST',
      body: JSON.stringify({ farmer_token: resolvedToken, source_mode: 'stored' }),
    });
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

export interface CopilotConversationResponse {
  reply: string;
  provider: string;
  model: string;
  safe_fallback: boolean;
  citations: Array<{ source_doc: string; chunk_id: string; quote: string }>;
  event_id?: string | null;
  disclaimer: string;
}

/** Send only the bounded conversation context; the provider key stays server-side. */
export async function sendCopilotMessage(
  message: string,
  locale: FarmerProfileDraft["locale"],
  history: CopilotMessage[],
): Promise<CopilotConversationResponse> {
  const farmerToken = await resolveFarmerToken();
  return request<CopilotConversationResponse>("/api/v1/copilot/chat", {
    method: "POST",
    body: JSON.stringify({
      farmer_token: farmerToken,
      message,
      locale,
      history: history.slice(-8).map((item) => ({
        role: item.role === "farmer" ? "user" : "assistant",
        content: item.text,
      })),
    }),
  });
}

export type SpeechLocale = FarmerProfileDraft["locale"];

const speechLanguage: Record<SpeechLocale, string> = {
  en: "en-IN",
  hi: "hi-IN",
  mr: "mr-IN",
};

function speechCode(locale: SpeechLocale) {
  return speechLanguage[locale];
}

async function blobAsDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => typeof reader.result === "string" ? resolve(reader.result) : reject(new Error("The recording could not be read."));
    reader.onerror = () => reject(new Error("The recording could not be read."));
    reader.readAsDataURL(blob);
  });
}

export interface SpeechTranscription {
  text: string;
  language_code: string | null;
  confidence: number | null;
}

/** Send a short browser recording to the server-side Sarvam STT adapter. */
export async function transcribeSpeech(blob: Blob, locale: SpeechLocale): Promise<SpeechTranscription> {
  if (!blob.size) throw new Error("The recording was empty. Try speaking again.");
  if (blob.size > 6_000_000) throw new Error("That recording is too long. Keep voice notes under one minute.");
  const farmerToken = await resolveFarmerToken();
  const response = await request<SpeechTranscription>("/api/v1/copilot/speech/transcribe", {
    method: "POST",
    body: JSON.stringify({
      farmer_token: farmerToken,
      audio_base64: await blobAsDataUrl(blob),
      audio_mime_type: blob.type || "audio/webm",
      language_code: speechCode(locale),
    }),
  });
  return response;
}

/** Ask the server-side Sarvam TTS adapter for WAV bytes. */
export async function synthesizeSpeech(text: string, locale: SpeechLocale): Promise<Blob> {
  const farmerToken = await resolveFarmerToken();
  const response = await requestResponse("/api/v1/copilot/speech/synthesize", {
    method: "POST",
    body: JSON.stringify({ farmer_token: farmerToken, text: text.trim(), language_code: speechCode(locale) }),
  });
  return response.blob();
}
