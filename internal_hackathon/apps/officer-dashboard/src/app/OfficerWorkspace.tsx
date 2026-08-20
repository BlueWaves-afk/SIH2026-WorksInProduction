import { useMemo, useRef, useState, type FormEvent } from "react";
import {
  Bell,
  ChevronDown,
  ChevronRight,
  CircleCheck,
  CircleHelp,
  Download,
  Info,
  LineChart,
  Mic,
  Paperclip,
  Pin,
  Plus,
  Search,
  SendHorizontal,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Star,
  Table2,
  MonitorUp,
  EyeOff,
  Database,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  ClipboardList,
  GitCompare,
  LayoutList,
} from "lucide-react";
import { GeoMap, type AlertCase, type CopilotBrief, type RiskEvent } from "ui-kit";
import type { DistrictHotspot } from "../api/client";
import { CHANNEL_LABEL, INTENT_LABEL, RESOLUTION_LABEL, demoComplaints, type ComplaintIntent } from "../demo";

type AnalysisTab = "summarize" | "compare" | "describe";
type StatusFilter = "open" | "new" | "breach" | "all";

const BAND_RANK: Record<string, number> = { red: 0, amber: 1, green: 2 };

/** module_5 §19 — Red first, then by confidence, then oldest first. */
function rankCases(list: AlertCase[]) {
  return [...list].sort((a, b) =>
    (BAND_RANK[a.band] - BAND_RANK[b.band]) ||
    (b.confidence - a.confidence) ||
    (Date.parse(a.sla_due_at ?? "") - Date.parse(b.sla_due_at ?? "")));
}

const STATUS_LABEL: Record<string, string> = {
  new: "New", acknowledged: "Acknowledged", visited: "Visited", referred: "Referred", resolved: "Resolved",
};

/** SLA target per module_5 §6.3: Red 24h, Amber 48h from creation. */
function slaState(item: AlertCase) {
  if (item.status === "resolved") return { label: "Closed", tone: "done" as const };
  if (!item.sla_due_at) return { label: "—", tone: "none" as const };
  const left = Date.parse(item.sla_due_at) - Date.now();
  if (left < 0) return { label: `${Math.round(-left / 3600_000)}h over`, tone: "breach" as const };
  return { label: `${Math.round(left / 3600_000)}h left`, tone: "ok" as const };
}


/** The five FDI signal families, in the order they appear in the comparison chart. */
const SIGNAL_FAMILIES = [
  { key: "rainfall", label: "Rainfall shock", tone: "violet", match: ["rainfall"] },
  { key: "price", label: "Price stress", tone: "teal", match: ["price"] },
  { key: "satellite", label: "Crop stress", tone: "slate", match: ["satellite", "crop"] },
  { key: "repayment", label: "Repayment window", tone: "amber", match: ["repayment", "irrigation"] },
  { key: "report", label: "Farmer report", tone: "pink", match: ["report", "farmer"] },
] as const;

function familyValue(event: RiskEvent, match: readonly string[]) {
  const hit = event.contributors.find((c) => match.some((m) => c.signal.includes(m)));
  if (!hit) return { points: 0, max: 20 };
  return { points: hit.points, max: hit.max_points || 20 };
}

export function OfficerWorkspace({
  cases, events, hotspots, eventById: eventMap, brief, selectedId, onSelect, onRequestBrief, loadingBrief,
  online, dataSourceLabel, dataError, onDismissError, lastPrompt, chatPrompt, onChatPrompt, onSubmitPrompt,
  onAcknowledge, onVisit, onRefer, onResolve,
}: {
  cases: AlertCase[];
  events: RiskEvent[];
  hotspots: DistrictHotspot[];
  eventById: Map<string, RiskEvent>;
  brief: CopilotBrief | null;
  selectedId: string;
  onSelect: (id: string) => void;
  onRequestBrief: () => void;
  loadingBrief: boolean;
  online: boolean;
  dataSourceLabel: string;
  dataError: string | null;
  onDismissError: () => void;
  lastPrompt: string | null;
  chatPrompt: string;
  onChatPrompt: (value: string) => void;
  onSubmitPrompt: (event: FormEvent<HTMLFormElement>) => void;
  onAcknowledge: () => void;
  onVisit: () => void;
  onRefer: () => void;
  onResolve: (code: string) => void;
}) {
  const [tab, setTab] = useState<AnalysisTab>("compare");
  const [analysisOpen, setAnalysisOpen] = useState(true);
  const [query, setQuery] = useState("");
  const [compareId, setCompareId] = useState(cases[0]?.case_id ?? "");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("open");
  const [resolution, setResolution] = useState("SUPPORT_PROVIDED");
  const [queueOpen, setQueueOpen] = useState(true);
  const [threadOpen, setThreadOpen] = useState(true);
  const [pinned, setPinned] = useState<Set<string>>(() => new Set());
  const [railOpen, setRailOpen] = useState(false);
  const [pinnedOnly, setPinnedOnly] = useState(false);
  const [infoOpen, setInfoOpen] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  const togglePin = (id: string) => setPinned((cur) => {
    const next = new Set(cur);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });

  const eventById = eventMap;
  const complaintByCase = useMemo(
    () => new Map(demoComplaints.map((c) => [c.case_id, c])),
    [],
  );
  const filtered = useMemo(() => cases.filter((c) => {
    const complaint = complaintByCase.get(c.case_id);
    const haystack = `${c.village_id} ${complaint?.farmer_label ?? ""} ${complaint ? INTENT_LABEL[complaint.intent] : ""}`.toLowerCase();
    if (!haystack.includes(query.toLowerCase())) return false;
    if (pinnedOnly && !pinned.has(c.case_id)) return false;
    if (statusFilter === "open") return c.status !== "resolved";
    if (statusFilter === "new") return c.status === "new";
    if (statusFilter === "breach") return slaState(c).tone === "breach";
    return true;
  }), [cases, query, statusFilter, complaintByCase, pinnedOnly, pinned]);
  const ranked = useMemo(() => {
    const base = rankCases(filtered);
    return [...base].sort((a, b) => Number(pinned.has(b.case_id)) - Number(pinned.has(a.case_id)));
  }, [filtered, pinned]);
  const resolved = cases.filter((c) => c.status === "resolved").length;
  const closurePct = cases.length ? Math.round((resolved / cases.length) * 100) : 0;
  const hotspot = useMemo(() => {
    const tally = new Map<string, number>();
    cases.filter((c) => c.status !== "resolved").forEach((c) => {
      const v = c.village_id.split(" / ").pop() ?? "";
      tally.set(v, (tally.get(v) ?? 0) + 1);
    });
    return [...tally.entries()].sort((a, b) => b[1] - a[1])[0];
  }, [cases]);
  const breaches = cases.filter((c) => slaState(c).tone === "breach").length;
  const newCount = cases.filter((c) => c.status === "new").length;
  const selected = cases.find((c) => c.case_id === selectedId) ?? cases[0];
  const selectedComplaint = selected ? complaintByCase.get(selected.case_id) : undefined;
  const selectedEvent = selected ? eventById.get(selected.event_id) : undefined;
  const compareCase = cases.find((c) => c.case_id === compareId) ?? cases[0];
  const compareEvent = compareCase ? eventById.get(compareCase.event_id) : undefined;

  const red = cases.filter((c) => c.band === "red").length;
  const amber = cases.filter((c) => c.band === "amber").length;
  const villages = [...new Set(cases.map((c) => c.village_id.split(" / ").pop()))];
  const hotspotPoints = hotspots.flatMap((item) => item.longitude == null || item.latitude == null ? [] : [{
    id: item.village_id,
    label: item.village_id.split(" / ").pop() ?? item.village_id,
    longitude: item.longitude,
    latitude: item.latitude,
    tone: item.red_cases > 0 ? "red" as const : "amber" as const,
    detail: `${item.open_cases} open · ${item.red_cases} red`,
  }]);

  return (
    <div className="ow">
      {dataError && (
        <div className="ow-error-banner" role="alert">
          <span><strong>Update not saved.</strong> {dataError}</span>
          <button type="button" onClick={onDismissError} aria-label="Dismiss error">Dismiss</button>
        </div>
      )}
      {/* ---------------------------------------------------------- icon rail */}
      <nav className={`ow-rail${railOpen ? " is-open" : ""}`} aria-label="Workspace navigation">
        <span className="ow-logo" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <path d="M20.5 5.5A11 11 0 1 0 20.5 26.5" stroke="url(#owG)" strokeWidth="4.2" strokeLinecap="round" />
            <rect x="17.5" y="12" width="3.4" height="8" rx="1.7" fill="url(#owG)" />
            <rect x="23" y="9" width="3.4" height="14" rx="1.7" fill="url(#owG)" />
            <defs>
              <linearGradient id="owG" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                <stop stopColor="#4f7dfb" /><stop offset="1" stopColor="#1b3fa8" />
              </linearGradient>
            </defs>
          </svg>
        </span>
        <button
          className={`ow-rail-expand${railOpen ? " is-open" : ""}`}
          aria-label={railOpen ? "Collapse navigation" : "Expand navigation"}
          aria-expanded={railOpen}
          onClick={() => setRailOpen((v) => !v)}
        >
          <ChevronRight size={17} strokeWidth={2.2} />
        </button>
        <div className="ow-rail-group">
          <button
            className={`ow-rail-btn is-solid${pinned.size ? " has-pins" : ""}`}
            aria-label={queueOpen ? "Collapse queue" : "Expand queue"}
            aria-pressed={!queueOpen}
            onClick={() => setQueueOpen((v) => !v)}
          >
            <Pin size={18} strokeWidth={1.9} /><span className="ow-rail-label">{queueOpen ? "Hide queue" : "Show queue"}</span>
          </button>
          {!queueOpen && pinned.size > 0 && (
            <div className="ow-rail-pins" aria-label="Pinned complaints">
              {ranked.filter((c) => pinned.has(c.case_id)).map((c) => (
                <button
                  key={c.case_id}
                  className={`ow-rail-pin band-${c.band}${c.case_id === selectedId ? " is-selected" : ""}`}
                  title={`${complaintByCase.get(c.case_id)?.farmer_label ?? c.case_id} · ${c.village_id.split(" / ").pop()}`}
                  onClick={() => onSelect(c.case_id)}
                />
              ))}
            </div>
          )}
          <button
            className={`ow-rail-btn${pinnedOnly ? " is-solid" : ""}`}
            aria-label={pinnedOnly ? "Show all complaints" : "Show pinned only"}
            aria-pressed={pinnedOnly}
            onClick={() => setPinnedOnly((v) => !v)}
          >
            <Star size={18} strokeWidth={1.9} /><span className="ow-rail-label">Pinned only</span>
          </button>
          <button
            className="ow-rail-btn"
            aria-label="Reset view"
            onClick={() => { setQuery(""); setStatusFilter("open"); setPinnedOnly(false); setQueueOpen(true); setThreadOpen(true); }}
          >
            <Plus size={18} strokeWidth={1.9} /><span className="ow-rail-label">Reset view</span>
          </button>
          <button
            className="ow-rail-btn"
            aria-label="Search complaints"
            onClick={() => { setQueueOpen(true); window.setTimeout(() => searchRef.current?.focus(), 0); }}
          >
            <SlidersHorizontal size={18} strokeWidth={1.9} /><span className="ow-rail-label">Search</span>
          </button>
          <span className="ow-rail-badge" title="Open complaints">{cases.filter((c) => c.status !== "resolved").length}</span>
        </div>
        <div className="ow-rail-foot">
          <button className="ow-rail-btn" aria-label="About this dashboard" aria-pressed={infoOpen} onClick={() => setInfoOpen((v) => !v)}>
            <CircleHelp size={18} strokeWidth={1.9} /><span className="ow-rail-label">About</span>
          </button>
          <button className="ow-rail-btn" aria-label="Data sources" onClick={() => setInfoOpen(true)}>
            <Info size={18} strokeWidth={1.9} /><span className="ow-rail-label">Sources</span>
          </button>
          <button
            className={`ow-rail-btn${breaches ? " has-alert" : ""}`}
            aria-label={`${breaches} complaints past SLA`}
            onClick={() => { setQueueOpen(true); setStatusFilter("breach"); }}
          >
            <Bell size={18} strokeWidth={1.9} /><span className="ow-rail-label">SLA breaches</span>
          </button>
          <span className="ow-avatar" aria-label="Officer Asha" />
        </div>
      </nav>

      <div className={`ow-stage${queueOpen ? "" : " is-queue-collapsed"}${threadOpen ? "" : " is-thread-collapsed"}`}>
      {/* ------------------------------------------------------ triage sidebar */}
      <aside className="ow-side" aria-label="Complaint triage">
        <header className="ow-side-head">
          <h2>Triage</h2>
          <span className="ow-side-count">{cases.filter((c) => c.status !== "resolved").length} open</span>
          <button className="ow-collapse" aria-label="Collapse queue" onClick={() => setQueueOpen(false)}>
            <PanelLeftClose size={16} strokeWidth={2} />
          </button>
        </header>

        <div className="ow-strip">
          <div><small>Urgent</small><strong>{red}</strong></div>
          <div><small>Awaiting ack</small><strong>{newCount}</strong></div>
          <div className={breaches ? "is-alert" : ""}><small>SLA breached</small><strong>{breaches}</strong></div>
          <div><small>Closure</small><strong>{closurePct}%</strong></div>
        </div>

        <label className="ow-search">
          <input ref={searchRef} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search complaints" aria-label="Search complaints" />
          <Search size={15} strokeWidth={2.1} />
        </label>

        <div className="ow-filters" role="group" aria-label="Filter complaints">
          {([["open", "Open"], ["new", "New"], ["breach", "SLA"], ["all", "All"]] as const).map(([k, label]) => (
            <button key={k} className={statusFilter === k ? "is-active" : ""} onClick={() => setStatusFilter(k)}>
              {label}
              {k === "breach" && breaches > 0 && <i>{breaches}</i>}
              {k === "new" && newCount > 0 && <i>{newCount}</i>}
            </button>
          ))}
        </div>

        <ul className="ow-queue" aria-label="Ranked complaint queue">
          {ranked.map((c) => {
            const complaint = complaintByCase.get(c.case_id);
            const sla = slaState(c);
            const ev = eventById.get(c.event_id);
            return (
              <li key={c.case_id} className={pinned.has(c.case_id) ? "is-pinned" : ""}>
                <button className={`ow-queue-row${c.case_id === selectedId ? " is-selected" : ""}`} onClick={() => onSelect(c.case_id)}>
                  <span className={`ow-queue-band band-${c.band}`} />
                  <span className="ow-queue-main">
                    <strong>{complaint ? INTENT_LABEL[complaint.intent] : "Signal-raised"}</strong>
                    <small>{complaint?.farmer_label ?? c.farmer_token.slice(0, 12)} · {c.village_id.split(" / ").pop()}</small>
                    <span className="ow-queue-drivers">
                      {(ev?.contributors ?? []).slice(0, 3).map((d) => (
                        <i key={d.signal} title={d.explanation}>{d.signal.replace(/_.*/, "")}</i>
                      ))}
                    </span>
                  </span>
                  <span className="ow-queue-meta">
                    <span className={`ow-status is-${c.status}`}>{STATUS_LABEL[c.status]}</span>
                    <span className={`ow-sla is-${sla.tone}`}>{sla.label}</span>
                  </span>
                </button>
                <button className="ow-pin" aria-label={pinned.has(c.case_id) ? "Unpin complaint" : "Pin complaint"}
                  aria-pressed={pinned.has(c.case_id)} onClick={() => togglePin(c.case_id)}>
                  <Pin size={13} strokeWidth={2.2} />
                </button>
              </li>
            );
          })}
          {!ranked.length && <li className="ow-queue-empty">No complaints in this view.</li>}
        </ul>
      </aside>

      {/* ------------------------------------------------------------- analysis */}
      <section className="ow-main" aria-label="Case analysis">
        {selected ? (
          <>
            <header className="ow-main-head">
              <div>
                <h1>{selectedComplaint ? INTENT_LABEL[selectedComplaint.intent] : "Signal-raised case"}</h1>
                <p>{selectedComplaint?.farmer_label ?? selected.farmer_token} · {selected.village_id} · {selected.case_id.replace("case-", "#")}</p>
              </div>
              <div className="ow-head-right">
                <span className={`ow-status is-${selected.status}`}>{STATUS_LABEL[selected.status]}</span>
                {!threadOpen && (
                  <button className="ow-collapse" aria-label="Expand copilot" onClick={() => setThreadOpen(true)}>
                    <PanelRightOpen size={16} strokeWidth={2} />
                  </button>
                )}
                <button className="ow-sources-btn" title={dataSourceLabel} aria-pressed={infoOpen} onClick={() => setInfoOpen((v) => !v)}><Database size={14} strokeWidth={2.1} /> Data sources</button>
              </div>
            </header>

            {infoOpen && (
              <div className="ow-info" role="note">
                <div className="ow-info-head">
                  <strong>Where this data comes from</strong>
                  <button onClick={() => setInfoOpen(false)} aria-label="Close">×</button>
                </div>
                <ul>
                  <li><b>IMD rainfall feed</b> — weather deviation vs. seasonal normal</li>
                  <li><b>Agmarknet</b> — mandi modal prices and arrivals</li>
                  <li><b>Sentinel-2</b> — satellite vegetation stress</li>
                  <li><b>Farmer reports</b> — missed call, IVR keypress and SMS replies</li>
                </ul>
                <p>Queue source: <b>{dataSourceLabel}</b>. Scores are produced by a deterministic rules engine, not a model, and are never a credit, loan-default or insurance score.</p>
              </div>
            )}

            {selectedComplaint && (
              <p className="ow-detail-quote">
                “{selectedComplaint.payload}”
                <em>{CHANNEL_LABEL[selectedComplaint.channel]} · {new Date(selectedComplaint.received_at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</em>
              </p>
            )}

            <div className="ow-block">
              <span className="ow-detail-label">Why this case is here</span>
              {(selectedEvent?.contributors ?? []).map((d) => (
                <div key={d.signal} className="ow-driver">
                  <span className="ow-driver-bar"><i style={{ width: `${Math.round((d.points / (d.max_points || 20)) * 100)}%` }} /></span>
                  <span className="ow-driver-text">{d.explanation}<small>{d.source}</small></span>
                  <b>+{Math.round(d.points)}</b>
                </div>
              ))}
              {selectedEvent && <p className="ow-detail-disclaimer">{selectedEvent.disclaimer}</p>}
            </div>

            <div className="ow-detail-actions">
              <button onClick={onAcknowledge} disabled={!online || selected.status !== "new"}>Acknowledge</button>
              <button onClick={onVisit} disabled={!online || selected.status === "resolved"}>Log visit</button>
              <button onClick={onRefer} disabled={!online || selected.status === "resolved"}>Refer to FPO/KVK</button>
              <span className="ow-detail-resolve">
                <select value={resolution} onChange={(e) => setResolution(e.target.value)} aria-label="Resolution code" disabled={selected.status === "resolved"}>
                  {Object.entries(RESOLUTION_LABEL).map(([code, label]) => <option key={code} value={code}>{label}</option>)}
                </select>
                <button className="is-primary" onClick={() => onResolve(resolution)} disabled={!online || selected.status === "resolved"}>Resolve</button>
              </span>
            </div>

            <div className="ow-block">
              <div className="ow-section-head">
                <div className="ow-section-toggle is-static"><Sparkles size={16} strokeWidth={2.1} /><h2>Analysis</h2></div>
                <button className="ow-hide-btn" onClick={() => setAnalysisOpen((v) => !v)}>
                  <EyeOff size={14} strokeWidth={2} /> {analysisOpen ? "hide" : "show"}
                </button>
              </div>

              {analysisOpen && (
                <>
                  <div className="ow-tabs">
                    <button className={tab === "summarize" ? "is-active" : ""} onClick={() => setTab("summarize")}><ClipboardList size={14} strokeWidth={2} />Summarize</button>
                    <button className={tab === "compare" ? "is-active" : ""} onClick={() => setTab("compare")}><GitCompare size={14} strokeWidth={2} />Explain key drivers</button>
                    <button className={tab === "describe" ? "is-active" : ""} onClick={() => setTab("describe")}><LayoutList size={14} strokeWidth={2} />Describe top cases</button>
                  </div>

                  <h3 className="ow-analysis-title">
                    {tab === "summarize" && `District position across ${villages.join(", ")}:`}
                    {tab === "compare" && `Comparison of the top ${Math.min(3, cases.length)} cases in Nashik:`}
                    {tab === "describe" && "What each case is telling us:"}
                  </h3>

                  {tab === "summarize" && hotspotPoints.length > 0 && (
                    <GeoMap points={hotspotPoints} center={[73.79, 20.22]} zoom={8.5} styleUrl={import.meta.env.VITE_MAP_STYLE_URL as string | undefined} label="Village support hotspots" privacyNote="Village centroids only" />
                  )}

                  <div className="ow-analysis-body">
                    <ul className="ow-case-list">
                      {cases.slice(0, 3).map((c) => {
                        const ev = eventById.get(c.event_id);
                        return (
                          <li key={c.case_id}>
                            <button onClick={() => { onSelect(c.case_id); setCompareId(c.case_id); }}>
                              <ChevronRight size={14} strokeWidth={2.4} />
                              <span>
                                <strong>{c.village_id.split(" / ").pop()} ({c.case_id.replace("case-", "#")})</strong>
                                <small>{ev?.contributors[0]?.explanation ?? "Awaiting signals."}</small>
                              </span>
                            </button>
                          </li>
                        );
                      })}
                    </ul>

                    <div className="ow-compare">
                      <div className="ow-compare-head">
                        <span>Compare</span>
                        <div className="ow-compare-tabs">
                          {cases.slice(0, 3).map((c) => (
                            <button key={c.case_id} className={c.case_id === compareId ? "is-active" : ""} onClick={() => setCompareId(c.case_id)}>
                              {c.village_id.split(" / ").pop()}
                            </button>
                          ))}
                        </div>
                      </div>
                      <ul className="ow-legend">
                        {SIGNAL_FAMILIES.map((f) => <li key={f.key}><i className={`tone-${f.tone}`} />{f.label}</li>)}
                      </ul>
                      <div className="ow-chart" role="img" aria-label="Signal contribution by family">
                        <div className="ow-chart-axis"><span>20</span><span>15</span><span>10</span><span>5</span><span>0</span></div>
                        <div className="ow-chart-bars">
                          {SIGNAL_FAMILIES.map((f) => {
                            const v = compareEvent ? familyValue(compareEvent, f.match) : { points: 0, max: 20 };
                            const pct = Math.max(6, Math.round((v.points / v.max) * 100));
                            return (
                              <div className="ow-bar" key={f.key}>
                                <span className="ow-bar-track" />
                                <span className={`ow-bar-fill tone-${f.tone}`} style={{ height: `${pct}%` }}><i /></span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </>
        ) : <p className="ow-detail-empty">Select a complaint from the queue.</p>}
      </section>

      {/* --------------------------------------------------------- agent panel */}
      <aside className="ow-thread" aria-label="Support copilot">
        <header className="ow-thread-head">
          <span>Copilot</span>
          <button className="ow-collapse" aria-label="Collapse copilot" onClick={() => setThreadOpen(false)}><PanelRightClose size={16} strokeWidth={2} /></button>
        </header>
        <div className="ow-thread-scroll">
          <span className="ow-thread-line" aria-hidden="true" />
          <div className="ow-msg is-user">Which cases need follow-up in Nashik?</div>
          <div className="ow-turn">
            <span className="ow-turn-mark is-done"><CircleCheck size={18} strokeWidth={2.2} /></span>
            <div className="ow-turn-body">
              <p className="ow-turn-lead">There are {cases.length} support cases open in Nashik district.</p>
              <p>
                Some examples are{" "}
                {cases.slice(0, 3).map((c, i) => (
                  <span key={c.case_id}>
                    <button className="ow-link" onClick={() => onSelect(c.case_id)}>
                      {c.village_id.split(" / ").pop()} ({c.case_id.replace("case-", "#")})
                    </button>
                    {i < 1 ? ", " : i === 1 ? ", and " : "."}
                  </span>
                ))}
              </p>
            </div>
          </div>

          <div className="ow-msg is-user">{lastPrompt ?? "Show me cases driven by rainfall deficit"}</div>

          <div className="ow-turn">
            <span className="ow-turn-mark is-brand">
              <svg viewBox="0 0 32 32" fill="none" width="15" height="15">
                <path d="M20.5 5.5A11 11 0 1 0 20.5 26.5" stroke="currentColor" strokeWidth="4.2" strokeLinecap="round" />
                <rect x="17.5" y="12" width="3.4" height="8" rx="1.7" fill="currentColor" />
                <rect x="23" y="9" width="3.4" height="14" rx="1.7" fill="currentColor" />
              </svg>
            </span>
            <div className="ow-turn-body">
              <span className="ow-unverified"><Info size={12} strokeWidth={2.4} /> Unverified</span>
              <p className="ow-turn-lead">
                There are {cases.filter((c) => eventById.get(c.event_id)?.contributors.some((d) => d.signal.includes("rainfall"))).length} cases with a rainfall-deficit driver:
              </p>
              <p>{brief ? brief.summary : "Rainfall deficit is reinforcing market and crop-stress signals in the urgent cases. An officer must confirm eligibility before any scheme is mentioned to the farmer."}</p>
              {brief?.scheme_matches.map((m) => (
                <p key={m.scheme} className="ow-cite"><button className="ow-link">{m.scheme}</button> — {m.why}</p>
              ))}
            </div>
          </div>

          {loadingBrief && (
            <div className="ow-turn">
              <span className="ow-turn-mark is-loading" />
              <div className="ow-turn-body"><p className="ow-analyzing">Analyzing the data…</p></div>
            </div>
          )}
        </div>

        <div className="ow-thread-foot">
          <div className="ow-suggest">
            <button onClick={onRequestBrief}>How many cases have a repayment window approaching…</button>
            <span>6+</span>
          </div>
          <form className="ow-ask" onSubmit={onSubmitPrompt}>
            <input value={chatPrompt} onChange={(e) => onChatPrompt(e.target.value)} placeholder="How can I help?" aria-label="Ask the support copilot" />
            <button type="button" className="ow-ask-icon" aria-label="Voice"><Mic size={17} strokeWidth={2} /></button>
            <button type="button" className="ow-ask-icon" aria-label="Attach"><Paperclip size={17} strokeWidth={2} /></button>
            <button className="ow-ask-send" type="submit" aria-label="Send"><SendHorizontal size={16} strokeWidth={2.2} /></button>
          </form>
          <p className="ow-sources">
            <button className="ow-link">IMD rainfall feed</button><span>, Weather</span>
            <i>•</i>
            <button className="ow-link">agmarknet.sql</button><span>, Market data</span>
            <span className="ow-sources-more">4+</span>
          </p>
        </div>
      </aside>
      </div>
    </div>
  );
}
