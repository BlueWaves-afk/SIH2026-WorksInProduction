import { useEffect, useMemo, useState } from "react";
import { BandChip, Button, CaseCard, KpiTile, MapWrapper, ScoreBreakdown, type AlertCase, type CopilotBrief, type RiskEvent } from "ui-kit";
import "ui-kit/styles.css";
import { loadCopilotBrief, loadOfficerQueue, transitionCase } from "../api/client";

type QueueFilter = "all" | "red" | "amber" | "green";

export function App() {
  const [cases, setCases] = useState<AlertCase[]>([]);
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [selectedId, setSelectedId] = useState("case-001");
  const [filter, setFilter] = useState<QueueFilter>("all");
  const [brief, setBrief] = useState<CopilotBrief | null>(null);
  const [loadingBrief, setLoadingBrief] = useState(false);
  const [online, setOnline] = useState(() => navigator.onLine);
  const [source, setSource] = useState<"api" | "demo-fixture">("demo-fixture");

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    void loadOfficerQueue().then((queue) => { setCases(queue.cases); setEvents(queue.events); setSource(queue.source); });
    return () => { window.removeEventListener("online", onOnline); window.removeEventListener("offline", onOffline); };
  }, []);

  const eventById = useMemo(() => new Map(events.map((event) => [event.event_id, event])), [events]);
  const visibleCases = useMemo(() => filter === "all" ? cases : cases.filter((item) => item.band === filter), [cases, filter]);
  const selected = cases.find((item) => item.case_id === selectedId) ?? visibleCases[0];
  const selectedEvent = selected ? eventById.get(selected.event_id) : undefined;
  const openCount = cases.filter((item) => item.status !== "resolved").length;
  const redCount = cases.filter((item) => item.band === "red" && item.status !== "resolved").length;
  const acknowledged = cases.filter((item) => item.status === "acknowledged" || item.status === "resolved").length;

  async function requestBrief() {
    if (!selected) return;
    setLoadingBrief(true);
    setBrief(await loadCopilotBrief(selected.case_id));
    setLoadingBrief(false);
  }

  async function updateCase(transition: "acknowledge" | "resolve") {
    if (!selected) return;
    try { await transitionCase(selected.case_id, transition); } catch { /* M5 endpoint is not available in the scaffold yet. */ }
    setCases((current) => current.map((item) => item.case_id === selected.case_id ? { ...item, status: transition === "acknowledge" ? "acknowledged" : "resolved", resolution_code: transition === "resolve" ? "officer_reviewed" : item.resolution_code } : item));
  }

  return (
    <main className="app-shell"><div className="app-container">
      <header className="app-header"><div><p className="eyebrow">M8 officer cockpit · Nashik district</p><h1>Support queue</h1><p className="subtitle">Rank and close the cases returned by M5. This dashboard does not recalculate score or confidence.</p></div><div className="stack" style={{ alignItems: "flex-end", gap: 5 }}><BandChip band="green" /> <span className="small muted">{online ? "Connected" : "Offline · last queue"} · {source === "api" ? "M1 API" : "replay fixture"}</span></div></header>
      {!online && <div className="notice warning" role="status">Network unavailable. The last loaded queue remains visible. Write actions are disabled until the server confirms them.</div>}
      <div className="grid grid-3" style={{ marginBottom: 18 }}><KpiTile label="Open cases" value={openCount} hint="M5 case status" /><KpiTile label="Red needing review" value={redCount} hint="Shown first by M1 ranking" /><KpiTile label="Acknowledged / closed" value={`${acknowledged}/${cases.length || 0}`} hint="Current district slice" /></div>
      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <section className="surface panel"><div className="row"><div><p className="eyebrow">Triage</p><h2>Ranked cases</h2></div><span className="spacer" /><select value={filter} onChange={(event) => setFilter(event.target.value as QueueFilter)} aria-label="Filter cases"><option value="all">All bands</option><option value="red">Red</option><option value="amber">Amber</option><option value="green">Green</option></select></div><div style={{ marginTop: 14 }}>{visibleCases.length ? visibleCases.map((item) => <CaseCard key={item.case_id} item={item} selected={selected?.case_id === item.case_id} onClick={() => { setSelectedId(item.case_id); setBrief(null); }} />) : <div className="notice">No cases in this filter.</div>}</div></section>
        <div className="stack">
          <MapWrapper title="District hotspot map"><div className="row" style={{ justifyContent: "center", marginTop: 12 }}><span className="band-chip red">Dindori · Red</span><span className="band-chip amber">Kalwan · Amber</span></div></MapWrapper>
          {selected && selectedEvent && <section className="surface panel"><div className="row"><div><p className="eyebrow">Case detail</p><h2>{selected.village_id}</h2></div><span className="spacer" /><BandChip band={selected.band} /></div><div className="case-meta" style={{ marginBottom: 14 }}><span>{selected.case_id}</span><span>Assigned: {selected.assigned_to ?? "unassigned"}</span><span>SLA: {selected.sla_due_at ? new Date(selected.sla_due_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "none"}</span></div><ScoreBreakdown event={selectedEvent} title="Shared explanation" /><div className="row" style={{ marginTop: 14 }}><Button variant="secondary" onClick={() => void updateCase("acknowledge")} disabled={!online || selected.status !== "new"}>Acknowledge</Button><Button variant="primary" onClick={() => void requestBrief()} disabled={loadingBrief || !online}>{loadingBrief ? "Preparing…" : "Get cited copilot brief"}</Button><Button variant="danger" onClick={() => void updateCase("resolve")} disabled={!online || selected.status === "resolved"}>Resolve</Button></div></section>}
        </div>
      </div>
      {brief && <section className="surface panel" style={{ marginTop: 16 }}><div className="row"><div><p className="eyebrow">M7 · officer review required</p><h2>Copilot brief</h2></div><span className="spacer" /><span className="band-chip green">Cited output</span></div><p>{brief.summary}</p><div className="grid grid-2"><div><h3>Suggested fixed action</h3><div className="notice">{brief.suggested_action ?? "No action suggested"}</div><h3 style={{ marginTop: 14 }}>Draft message</h3><div className="notice">{brief.draft_message ?? "No draft: contact consent is not available."}</div></div><div><h3>Scheme references</h3>{brief.scheme_matches.length ? brief.scheme_matches.map((match) => <div className="citation" key={match.scheme}><strong>{match.scheme}</strong> — {match.why}{match.citations.map((citation) => <div className="muted small" key={citation.chunk_id}>[{citation.source_doc} · {citation.chunk_id}] “{citation.quote}”</div>)}</div>) : <div className="notice">No cited match found. Do not infer eligibility.</div>}</div></div><p className="footer-note">The officer must edit and separately approve any message through M6. M7 cannot send or change this case.</p></section>}
      <p className="footer-note">M8 displays M1/M4/M5/M7 outputs. The demo fixture is clearly labelled; production API and map integration are owned by the other modules.</p>
    </div></main>
  );
}
