import { useEffect, useMemo, useState, type FormEvent } from "react";
import type { AlertCase, CopilotBrief, RiskEvent } from "ui-kit";
import "ui-kit/styles.css";
import "ui-kit/officer-workspace.css";
import { loadCopilotBrief, loadOfficerQueue, transitionCase, type DistrictHotspot, type OfficerQueue } from "../api/client";
import { OfficerWorkspace } from "./OfficerWorkspace";
import { demoMode } from "../auth/supabase";

/**
 * Data + case-transition layer for the officer workspace.
 * All presentation lives in <OfficerWorkspace />.
 */
export function App() {
  const [cases, setCases] = useState<AlertCase[]>([]);
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [hotspots, setHotspots] = useState<DistrictHotspot[]>([]);
  const [selectedId, setSelectedId] = useState("case-001");
  const [brief, setBrief] = useState<CopilotBrief | null>(null);
  const [chatPrompt, setChatPrompt] = useState("");
  const [lastPrompt, setLastPrompt] = useState<string | null>(null);
  const [loadingBrief, setLoadingBrief] = useState(false);
  const [queueSource, setQueueSource] = useState<OfficerQueue["source"]>("demo-fixture");
  const [online, setOnline] = useState(() => navigator.onLine);
  const [loadingQueue, setLoadingQueue] = useState(true);
  const [dataError, setDataError] = useState<string | null>(null);

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    void refreshQueue();
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  async function refreshQueue() {
    setLoadingQueue(true);
    setDataError(null);
    try {
      const queue = await loadOfficerQueue();
      setCases(queue.cases);
      setEvents(queue.events);
      setHotspots(queue.hotspots);
      setQueueSource(queue.source);
    } catch (reason) {
      setDataError(reason instanceof Error ? reason.message : "The district queue is unavailable.");
    } finally {
      setLoadingQueue(false);
    }
  }

  const eventById = useMemo(() => new Map(events.map((event) => [event.event_id, event])), [events]);
  const selected = cases.find((item) => item.case_id === selectedId) ?? cases[0];
  const dataSourceLabel = queueSource === "api" ? "Live district feed" : "Replay fixture";

  async function requestBrief(prompt?: string) {
    if (!selected) return;
    setDataError(null);
    setLoadingBrief(true);
    if (prompt) setLastPrompt(prompt);
    try {
      setBrief(await loadCopilotBrief(selected.case_id));
    } catch (reason) {
      setDataError(reason instanceof Error ? reason.message : "The copilot brief is unavailable.");
    } finally {
      setLoadingBrief(false);
    }
  }

  async function updateCase(transition: "acknowledge" | "visit" | "refer" | "resolve", code?: string) {
    if (!selected) return;
    setDataError(null);
    try {
      await transitionCase(selected.case_id, transition);
    } catch (reason) {
      if (!demoMode) {
        setDataError(reason instanceof Error ? reason.message : "The case update was not saved.");
        return;
      }
    }
    const nextStatus = { acknowledge: "acknowledged", visit: "visited", refer: "referred", resolve: "resolved" } as const;
    setCases((current) => current.map((item) => item.case_id === selected.case_id
      ? {
          ...item,
          status: nextStatus[transition],
          resolution_code: transition === "resolve" ? (code ?? "SUPPORT_PROVIDED") : item.resolution_code,
        }
      : item));
  }

  function chooseCase(caseId: string) {
    setSelectedId(caseId);
    setBrief(null);
    setLastPrompt(null);
  }

  function submitPrompt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = chatPrompt.trim() || `Explain the strongest support signals for ${selected?.village_id ?? "this case"}.`;
    setChatPrompt("");
    void requestBrief(prompt);
  }

  if (loadingQueue && cases.length === 0) {
    return <main className="auth-page is-officer"><section className="auth-card"><p className="auth-kicker">DISTRICT OPERATIONS</p><h1>Loading the case queue…</h1></section></main>;
  }
  if (dataError && cases.length === 0) {
    return <main className="auth-page is-officer"><section className="auth-card"><p className="auth-kicker">CONNECTION NEEDED</p><h1>The officer queue is unavailable.</h1><p>{dataError}</p><button className="auth-submit" onClick={() => void refreshQueue()}>Try again</button></section></main>;
  }

  return (
    <OfficerWorkspace
      cases={cases}
      events={events}
      hotspots={hotspots}
      eventById={eventById}
      brief={brief}
      selectedId={selected?.case_id ?? selectedId}
      onSelect={chooseCase}
      onRequestBrief={() => void requestBrief()}
      loadingBrief={loadingBrief}
      online={online}
      dataSourceLabel={dataSourceLabel}
      dataError={dataError}
      onDismissError={() => setDataError(null)}
      lastPrompt={lastPrompt}
      chatPrompt={chatPrompt}
      onChatPrompt={setChatPrompt}
      onSubmitPrompt={submitPrompt}
      onAcknowledge={() => void updateCase("acknowledge")}
      onVisit={() => void updateCase("visit")}
      onRefer={() => void updateCase("refer")}
      onResolve={(code) => void updateCase("resolve", code)}
    />
  );
}
