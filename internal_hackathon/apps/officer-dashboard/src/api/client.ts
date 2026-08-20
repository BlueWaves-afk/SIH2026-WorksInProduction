import type { AlertCase, CopilotBrief, RiskEvent } from "ui-kit";
import { accessToken, demoMode } from "../auth/supabase";
import { demoBrief, demoCases, demoEvents, demoExtraCases } from "../demo";

export interface DistrictHotspot { village_id: string; open_cases: number; red_cases: number; latitude: number | null; longitude: number | null; precision: "village_centroid"; }
export interface OfficerQueue { cases: AlertCase[]; events: RiskEvent[]; hotspots: DistrictHotspot[]; source: "api" | "demo-fixture"; cached_at: string; }

const demoHotspots: DistrictHotspot[] = [
  { village_id: "Nashik / Dindori", open_cases: 2, red_cases: 1, latitude: 20.205, longitude: 73.827, precision: "village_centroid" },
  { village_id: "Nashik / Kalwan", open_cases: 2, red_cases: 0, latitude: 20.492, longitude: 74.026, precision: "village_centroid" },
  { village_id: "Nashik / Peint", open_cases: 1, red_cases: 1, latitude: 20.258, longitude: 73.503, precision: "village_centroid" },
];

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

export async function loadOfficerQueue(): Promise<OfficerQueue> {
  try {
    const [events, cases, analytics] = await Promise.all([
      request<{ items: RiskEvent[] }>("/api/v1/risk-events?limit=100"),
      request<{ items: AlertCase[] }>("/api/v1/cases?limit=100"),
      request<{ hotspots: DistrictHotspot[] }>("/api/v1/analytics/district"),
    ]);
    return { cases: cases.items, events: events.items, hotspots: analytics.hotspots, source: "api", cached_at: new Date().toISOString() };
  } catch {
    if (demoMode) return { cases: [...demoCases, ...demoExtraCases], events: demoEvents, hotspots: demoHotspots, source: "demo-fixture", cached_at: new Date().toISOString() };
    throw new Error("The district queue is unavailable. Check the backend connection and try again.");
  }
}

export async function loadCopilotBrief(caseId: string): Promise<CopilotBrief> {
  try {
    return await request<CopilotBrief>("/api/v1/copilot/brief", { method: "POST", body: JSON.stringify({ case_id: caseId }) });
  } catch {
    if (demoMode) return { ...demoBrief, case_id: caseId };
    throw new Error("The copilot brief is unavailable. No draft was generated.");
  }
}

/** module_5 §6: the four officer transitions. */
export type CaseTransition = "acknowledge" | "visit" | "refer" | "resolve";

export async function transitionCase(caseId: string, transition: CaseTransition): Promise<void> {
  if (transition === "acknowledge" || transition === "resolve") {
    const body = transition === "resolve" ? { resolution_code: "supported" } : undefined;
    await request(`/api/v1/cases/${caseId}/${transition}`, { method: "POST", ...(body ? { body: JSON.stringify(body) } : {}) });
    return;
  }
  await request(`/api/v1/cases/${caseId}/transition`, { method: "POST", body: JSON.stringify({ status: transition === "visit" ? "visited" : "referred" }) });
}
