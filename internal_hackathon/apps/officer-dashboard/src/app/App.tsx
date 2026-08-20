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
  const [draftMessage, setDraftMessage] = useState("");
  const [loadingBrief, setLoadingBrief] = useState(false);
  const [approved, setApproved] = useState(false);
  const [online, setOnline] = useState(() => navigator.onLine);

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    void loadOfficerQueue().then((queue) => { setCases(queue.cases); setEvents(queue.events); });
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
    setApproved(false);
    const result = await loadCopilotBrief(selected.case_id);
    setBrief(result);
    setDraftMessage(result.draft_message ?? "");
    setLoadingBrief(false);
  }

  async function updateCase(transition: "acknowledge" | "resolve") {
    if (!selected) return;
    try { await transitionCase(selected.case_id, transition); } catch { /* The interface remains useful when the write endpoint is unavailable. */ }
    setCases((current) => current.map((item) => item.case_id === selected.case_id ? { ...item, status: transition === "acknowledge" ? "acknowledged" : "resolved", resolution_code: transition === "resolve" ? "officer_reviewed" : item.resolution_code } : item));
  }

  function chooseCase(caseId: string) {
    setSelectedId(caseId);
    setBrief(null);
    setDraftMessage("");
    setApproved(false);
  }

  return (
    <main className="app-shell officer-shell"><div className="app-container">
      <header className="app-header officer-header"><div><div className="mobile-topline"><span className="location-pill"><span className="location-dot" /> Nashik district</span><span className="copilot-status">{online ? "Queue updated" : "Last saved queue"}</span></div><p className="eyebrow">Field support</p><h1>Cases requiring follow-up</h1><p className="subtitle">Review the strongest support signals, understand what is driving them, and close the loop with the right person.</p></div></header>
      {!online && <div className="notice warning" role="status">You are offline. The last saved queue is available; updates will resume when the connection returns.</div>}
      <div className="metric-strip" style={{ marginBottom: 18 }}><KpiTile label="Open cases" value={openCount} hint="Need a next step" /><KpiTile label="Urgent review" value={redCount} hint="Highest support need" /><KpiTile label="Acknowledged" value={`${acknowledged}/${cases.length || 0}`} hint="Already picked up" /></div>
      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <section className="surface panel"><div className="queue-heading"><div><p className="eyebrow">Your queue</p><h2>Prioritised cases</h2></div><span className="spacer" /><select className="select-control" value={filter} onChange={(event) => setFilter(event.target.value as QueueFilter)} aria-label="Filter cases"><option value="all">All cases</option><option value="red">Urgent</option><option value="amber">Watch</option><option value="green">Stable</option></select></div><p className="muted small" style={{ marginTop: 7, marginBottom: 0 }}>Start with urgent cases, then work down the list.</p><div style={{ marginTop: 14 }}>{visibleCases.length ? visibleCases.map((item) => <CaseCard key={item.case_id} item={item} selected={selected?.case_id === item.case_id} onClick={() => chooseCase(item.case_id)} />) : <div className="notice">No cases in this view.</div>}</div></section>
        <div className="stack">
          <MapWrapper title="Village overview"><div className="row" style={{ justifyContent: "center", marginTop: 12 }}><span className="band-chip red">Dindori · Urgent</span><span className="band-chip amber">Kalwan · Watch</span></div></MapWrapper>
          {selected && selectedEvent && <section className="surface panel"><div className="row"><div><p className="eyebrow">Selected case</p><h2>{selected.village_id}</h2></div><span className="spacer" /><BandChip band={selected.band} /></div><div className="case-meta" style={{ marginBottom: 14 }}><span>{Math.round(selected.confidence * 100)}% confidence</span><span>Assigned: {selected.assigned_to ?? "unassigned"}</span><span>SLA: {selected.sla_due_at ? new Date(selected.sla_due_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "none"}</span></div><ScoreBreakdown event={selectedEvent} title="Why this case is here" /><div className="case-detail-actions" style={{ marginTop: 14 }}><Button variant="secondary" onClick={() => void updateCase("acknowledge")} disabled={!online || selected.status !== "new"}>Acknowledge</Button><Button variant="primary" onClick={() => void requestBrief()} disabled={loadingBrief || !online}>{loadingBrief ? "Preparing…" : "Ask support copilot"}</Button><Button variant="danger" onClick={() => void updateCase("resolve")} disabled={!online || selected.status === "resolved"}>Resolve</Button></div></section>}
        </div>
      </div>
      {brief && <section className="surface panel copilot-panel" style={{ marginTop: 16 }}><div className="row"><div><p className="eyebrow">Support copilot</p><h2>Review a safe next step</h2></div><span className="spacer" /><span className="band-chip green">Sources attached</span></div><p>{brief.summary}</p><div className="grid grid-2"><div><h3>Suggested action</h3><div className="notice">{brief.suggested_action ?? "No action suggested"}</div><h3 style={{ marginTop: 14 }}>Message for the farmer</h3><textarea className="copilot-textarea" aria-label="Message for the farmer" value={draftMessage} onChange={(event) => { setDraftMessage(event.target.value); setApproved(false); }} placeholder="Add a short, clear message…" /><div className="row" style={{ marginTop: 10 }}><Button variant="primary" onClick={() => setApproved(true)} disabled={!draftMessage.trim() || !online}>{approved ? "Approved for delivery" : "Approve message"}</Button>{approved && <span className="small muted">Ready for the delivery service.</span>}</div></div><div><h3>References</h3>{brief.scheme_matches.length ? brief.scheme_matches.map((match) => <div className="citation" key={match.scheme}><strong>{match.scheme}</strong> — {match.why}{match.citations.map((citation) => <div className="muted small" key={citation.chunk_id}>[{citation.source_doc} · {citation.chunk_id}] “{citation.quote}”</div>)}</div>) : <div className="notice">No verified match found. Do not infer eligibility.</div>}</div></div><p className="footer-note">Edit every message before it is delivered. The copilot can explain and draft; the officer stays in control.</p></section>}
      <p className="footer-note">Support decisions are recorded with their reason, owner and outcome.</p>
    </div></main>
  );
}
