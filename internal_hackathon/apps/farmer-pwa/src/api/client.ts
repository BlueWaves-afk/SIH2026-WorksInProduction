import type { ActionCard, ConsentState, MandiQuote, RiskEvent } from "ui-kit";
import { demoActionCard, demoMandis, demoRiskEvent } from "../demo";

export interface FarmerProfileDraft {
  locale: "hi" | "mr" | "en";
  crop: string;
  season: string;
  irrigation: string;
  consent_flags: ConsentState;
}

export interface FarmerStatus {
  risk_event: RiskEvent;
  action_card: ActionCard;
  mandis: MandiQuote[];
  cached_at: string;
  source: "api" | "demo-fixture";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json() as Promise<T>;
}

export async function submitFarmerProfile(draft: FarmerProfileDraft): Promise<void> {
  await request("/api/v1/farmer-profiles", { method: "POST", body: JSON.stringify(draft) });
}

export async function loadFarmerStatus(): Promise<FarmerStatus> {
  try {
    const payload = await request<{ risk_event: RiskEvent; action_card: ActionCard; mandis: MandiQuote[] }>("/api/v1/risk-events?scope=farmer");
    return { ...payload, cached_at: new Date().toISOString(), source: "api" };
  } catch {
    return { risk_event: demoRiskEvent, action_card: demoActionCard, mandis: demoMandis, cached_at: new Date().toISOString(), source: "demo-fixture" };
  }
}
