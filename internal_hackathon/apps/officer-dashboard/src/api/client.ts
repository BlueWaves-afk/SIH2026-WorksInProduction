import type { AlertCase, CopilotBrief, RiskEvent } from "ui-kit";
import { demoBrief, demoCases, demoEvents } from "../demo";

export interface OfficerQueue { cases: AlertCase[]; events: RiskEvent[]; source: "api" | "demo-fixture"; cached_at: string; }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json() as Promise<T>;
}

export async function loadOfficerQueue(): Promise<OfficerQueue> {
  try {
    const payload = await request<{ cases: AlertCase[]; events: RiskEvent[] }>("/api/v1/risk-events?district_id=demo");
    return { ...payload, source: "api", cached_at: new Date().toISOString() };
  } catch {
    return { cases: demoCases, events: demoEvents, source: "demo-fixture", cached_at: new Date().toISOString() };
  }
}

export async function loadCopilotBrief(caseId: string): Promise<CopilotBrief> {
  try {
    return await request<CopilotBrief>("/api/v1/copilot/brief", { method: "POST", body: JSON.stringify({ case_id: caseId }) });
  } catch {
    return { ...demoBrief, case_id: caseId };
  }
}

export async function transitionCase(caseId: string, transition: "acknowledge" | "resolve"): Promise<void> {
  await request(`/api/v1/cases/${caseId}/${transition}`, { method: "POST" });
}
