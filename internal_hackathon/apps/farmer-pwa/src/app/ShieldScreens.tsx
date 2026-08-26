import { useEffect, useState } from "react";
import {
  ArrowLeft,
  AudioLines,
  CircleAlert,
  BellRing,
  Bot,
  CalendarClock,
  Check,
  ChevronRight,
  CircleCheckBig,
  CloudRain,
  Headphones,
  IndianRupee,
  Languages,
  LockKeyhole,
  LogOut,
  MapPin,
  MessageCircle,
  Mic,
  MoreHorizontal,
  PhoneCall,
  Radio,
  Search,
  SlidersHorizontal,
  SendHorizontal,
  ShieldCheck,
  Sprout,
  Square,
  Share2,
  Store,
  ThumbsUp,
  UserRound,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { useT } from "../i18n";
import { ConsentToggle, GeoMap, type ActionCard, type ConsentState, type Contributor, type CopilotMessage, type MandiQuote, type RiskEvent } from "ui-kit";

function InnerHeader({ title, subtitle, onBack }: { title: string; subtitle?: string; onBack: () => void }) {
  return (
    <header className="shield-inner-header">
      <button onClick={onBack} aria-label="Go back"><ArrowLeft size={20} /></button>
      <span><h1>{title}</h1>{subtitle && <small>{subtitle}</small>}</span>
      <button className="shield-inner-mark" aria-label="KisanSetu"><span className="shield-inner-mark-logo" aria-hidden="true" /></button>
    </header>
  );
}

const DRIVER_ICONS: Record<string, typeof CloudRain> = {
  rainfall_deficit: CloudRain,
  rainfall_excess: CloudRain,
  satellite_crop_stress: Sprout,
  price_shock: IndianRupee,
  repayment_window: CalendarClock,
  farmer_report: MessageCircle,
};

type TimelineKind = "officer" | "farmer" | "signal";

interface TimelineEntry {
  id: string;
  kind: TimelineKind;
  date: string;
  text: string;
  grade?: "healthy" | "stress" | "severe";
  signal?: string;
}

function formatDay(iso: string, offsetDays = 0) {
  const date = new Date(iso);
  date.setDate(date.getDate() - offsetDays);
  return date.toLocaleDateString("en-IN", { weekday: "short", month: "short", day: "2-digit", year: "numeric" });
}

/** Merges the three things a farmer actually needs to see in order:
 *  what the officer did, what the farmer reported, and which signals fired. */
function buildTimeline(event: RiskEvent, t: (k: string) => string): TimelineEntry[] {
  const base = event.evaluated_at ?? event.contributors[0]?.observed_at ?? new Date().toISOString();
  // Thumbnail severity mirrors how hard the signal actually fired.
  const gradeFor = (driver: Contributor): "healthy" | "stress" | "severe" => {
    const ratio = driver.max_points ? driver.points / driver.max_points : 0;
    return ratio >= 0.85 ? "severe" : ratio >= 0.6 ? "stress" : "healthy";
  };
  return [
    { id: "officer-ack", kind: "officer", date: formatDay(base), text: t("timeline.officer") },
    { id: "farmer-report", kind: "farmer", date: formatDay(base), text: t("timeline.farmer") },
    ...event.contributors.map((driver, index) => ({
      id: `${driver.signal}-${index}`,
      kind: "signal" as const,
      date: formatDay(driver.observed_at, index),
      text: driver.explanation,
      grade: gradeFor(driver),
      signal: driver.signal,
    })),
  ];
}

function TimelineMedia({ entry }: { entry: TimelineEntry }) {
  if (entry.kind === "officer") {
    return (
      <span className="shield-tl-media is-stack" aria-hidden="true">
        <i className="m-officer" /><i className="m-farmer" />
        <b><Radio size={9} strokeWidth={2.6} /></b>
      </span>
    );
  }
  if (entry.kind === "farmer") {
    return <span className="shield-tl-media is-avatar" aria-hidden="true"><UserRound size={17} strokeWidth={1.9} /></span>;
  }
  return <span className={`shield-tl-media is-thumb grade-${entry.grade} signal-${entry.signal ?? "unknown"}`} aria-hidden="true" />;
}

export function ShieldStatusScreen({ event, onBack, onAsk }: { event: RiskEvent; onBack: () => void; onAsk: () => void }) {
  const t = useT();
  const entries = buildTimeline(event, t);
  const top = event.contributors.slice(0, 2).map((driver) => driver.explanation.toLowerCase()).join(", ");

  return (
    <div className="shield-screen shield-signal-screen">
      <section className="shield-signal-hero">
        <button className="shield-hero-back" onClick={onBack}><ArrowLeft size={19} strokeWidth={2.2} /> {t("timeline.back")}</button>
        <button className="shield-hero-more" aria-label="More options"><MoreHorizontal size={20} strokeWidth={2.2} /></button>
        <div className="shield-hero-footer">
          <span className="shield-hero-pill is-score"><CircleAlert size={14} strokeWidth={2.4} /> {event.score}/100</span>
          <span className="shield-hero-pill is-live"><i /> Live</span>
          <span className="shield-hero-stats">
            <span><ThumbsUp size={15} strokeWidth={2.2} /> {Math.round(event.confidence * 100)}</span>
            <span><MessageCircle size={15} strokeWidth={2.2} /> {event.contributors.length}</span>
          </span>
        </div>
      </section>

      <section className="shield-signal-intro">
        <h1>{t("timeline.heading")}</h1>
        <p>Support was raised for your cotton plot in {event.village_id}. {top ? `Drivers: ${top}.` : ""} An agriculture officer has been notified and your case is being tracked to closure.</p>
      </section>

      <div className="shield-signal-timeline">
        {entries.map((entry, index) => (
          <article className={`shield-tl-item ${index === 0 ? "is-active" : ""}`} key={entry.id}>
            <span className="shield-tl-date"><i /> {entry.date}</span>
            <div className="shield-tl-bubble">
              <TimelineMedia entry={entry} />
              <p>{entry.text}</p>
            </div>
          </article>
        ))}
      </div>

      <div className="shield-safety-note"><LockKeyhole size={18} /><span><strong>{t("timeline.safety.title")}</strong><small>{event.disclaimer}</small></span></div>

      <div className="shield-signal-footer">
        <button className="shield-signal-share" aria-label="Share this timeline"><Share2 size={19} strokeWidth={2.1} /></button>
        <button className="shield-signal-chat" onClick={onAsk}>
          <span>{t("timeline.chat")}</span>
          <span className="shield-chat-icon" aria-hidden="true"><AudioLines size={17} strokeWidth={2.3} /></span>
        </button>
      </div>
    </div>
  );
}

export function ShieldActionScreen({ card, onBack, onAsk }: { card: ActionCard; onBack: () => void; onAsk: () => void }) {
  return (
    <div className="shield-screen">
      <InnerHeader title="Today’s plan" subtitle="Reviewed guidance" onBack={onBack} />
      <section className="shield-plan-hero">
        <span><CircleCheckBig size={28} /></span>
        <div><small>SAFE NEXT STEPS</small><h1>{card.title}</h1><p>Complete these in order. You remain in control of every action.</p></div>
        <b>{card.steps.length}</b>
      </section>
      <section className="shield-action-list">
        {card.steps.map((step, index) => (
          <article className="shield-action-item" key={`${card.card_id}-${index}`}>
            <span>{index + 1}</span>
            <div><small>{index === 0 ? "DO THIS FIRST" : index === 1 ? "THEN COMPARE" : "ASK FOR SUPPORT"}</small><strong>{step.text}</strong></div>
            <button aria-label={`Mark step ${index + 1} complete`}><Check size={17} /></button>
          </article>
        ))}
      </section>
      <div className="shield-review-line"><ShieldCheck size={17} /><span>Reviewed by {card.approved_by}</span></div>
      <button className="shield-primary-cta" onClick={onAsk}><Bot size={18} /> Ask the copilot about this plan</button>
    </div>
  );
}

export function ShieldMarketScreen({ mandis, onBack }: { mandis: MandiQuote[]; onBack: () => void }) {
  const t = useT();
  const mapPoints = [
    { id: "current-area", label: "Dindori area", longitude: 73.84, latitude: 20.22, tone: "current" as const, detail: "Approximate location" },
    ...mandis.flatMap((mandi) => mandi.longitude == null || mandi.latitude == null ? [] : [{ id: mandi.mandi, label: mandi.mandi, longitude: mandi.longitude, latitude: mandi.latitude, tone: "green" as const, detail: `₹${mandi.modal_price.toLocaleString("en-IN")} modal price` }]),
  ];
  return (
    <div className="shield-screen">
      <InnerHeader title={t("menu.markets")} subtitle={t("menu.markets.sub")} onBack={onBack} />
      <label className="shield-search"><Search size={18} /><input aria-label="Search markets" placeholder={t("copilot.search")} /><button aria-label="Market filters">⌁</button></label>
      <GeoMap points={mapPoints} center={[73.84, 20.22]} zoom={9} styleUrl={import.meta.env.VITE_MAP_STYLE_URL as string | undefined} label="Nearby public markets" privacyNote="Approximate farmer area" />
      <section className="shield-market-list">
        <div className="shield-section-heading"><div><span>{t("markets.priceOptions")}</span><h2>{t("markets.nearYou")}</h2></div><b>Today</b></div>
        {mandis.map((mandi, index) => (
          <article key={mandi.mandi} className={`shield-market-row ${index === 1 ? "best" : ""}`}>
            <span className="shield-market-rank">{index === 1 ? <ShieldCheck size={18} /> : index + 1}</span>
            <span><strong>{mandi.mandi}</strong><small><MapPin size={12} /> {mandi.distance_km} km away · verified today</small></span>
            <span><strong>₹{mandi.modal_price.toLocaleString("en-IN")}</strong><small>{mandi.change_pct}% seasonal</small></span>
          </article>
        ))}
      </section>
      <div className="shield-safety-note"><IndianRupee size={18} /><span><strong>{t("markets.compare")}</strong><small>{t("markets.compareSub")}</small></span></div>
    </div>
  );
}

const WAVE_POINTS = "0.0,41.04 1.5,46.61 3.0,51.21 4.5,50.59 6.0,44.61 7.5,36.46 9.0,28.94 10.5,23.88 12.0,22.87 13.5,25.09 15.0,26.39 16.5,24.04 18.0,21.24 19.5,22.91 21.0,28.07 22.5,30.82 24.0,29.01 25.5,26.87 27.0,27.91 28.5,29.71 30.0,28.79 31.5,26.31 33.0,25.45 34.5,25.64 36.0,23.91 37.5,20.39 39.0,18.64 40.5,20.87 42.0,26.15 43.5,32.66 45.0,38.4 46.5,40.28 48.0,36.62 49.5,31.03 51.0,29.68 52.5,33.65 54.0,37.66 55.5,38.1 57.0,37.92 58.5,40.91 60.0,44.96 61.5,45.21 63.0,41.39 64.5,37.28 66.0,34.08 67.5,29.31 69.0,22.34 70.5,16.54 72.0,14.74 73.5,15.93 75.0,17.69 76.5,18.91 78.0,18.93 79.5,17.37 81.0,16.6 82.5,20.83 84.0,30.04 85.5,37.96 87.0,39.21 88.5,35.94 90.0,33.88 91.5,33.9 93.0,32.42 94.5,28.89 96.0,27.41 97.5,30.13 99.0,33.84 100.5,35.27 102.0,35.62 103.5,37.31 105.0,39.4 106.5,39.18 108.0,36.19 109.5,31.98 111.0,27.87 112.5,25.56 114.0,27.65 115.5,34.0 117.0,39.2 118.5,37.94 120.0,32.04 121.5,28.04 123.0,28.18 124.5,28.28 126.0,25.33 127.5,21.93 129.0,21.02 130.5,20.65 132.0,17.68 133.5,13.66 135.0,12.88 136.5,16.2 138.0,20.78 139.5,24.85 141.0,29.11 142.5,34.02 144.0,38.94 145.5,43.93 147.0,48.67 148.5,50.0 150.0,44.74 151.5,35.58 153.0,30.0 154.5,31.43 156.0,35.39 157.5,36.4 159.0,35.06 160.5,34.78 162.0,34.88 163.5,32.03 165.0,26.75 166.5,23.44 168.0,23.9 169.5,25.18 171.0,24.57 172.5,23.08 174.0,22.66 175.5,23.47 177.0,25.21 178.5,27.93 180.0,30.05 181.5,28.9 183.0,25.32 184.5,24.42 186.0,28.74 187.5,33.52 189.0,32.56 190.5,26.63 192.0,21.73 193.5,20.66 195.0,21.13 196.5,22.08 198.0,26.27 199.5,34.79 201.0,43.46 202.5,47.6 204.0,47.3 205.5,45.62 207.0,43.9 208.5,41.82 210.0,39.56 211.5,37.05 213.0,32.96 214.5,27.56 216.0,24.54 217.5,26.47 219.0,29.66 220.5,27.99 222.0,21.48 223.5,16.41 225.0,16.53 226.5,18.89 228.0,19.87 229.5,20.61 231.0,23.4 232.5,26.3 234.0,25.95 235.5,23.38 237.0,23.04 238.5,26.93 240.0,32.98 241.5,38.62 243.0,42.44 244.5,43.03 246.0,39.95 247.5,35.97 249.0,34.5 250.5,34.39 252.0,31.26 253.5,25.04 255.0,21.76 256.5,25.62 258.0,33.04 259.5,37.95 261.0,39.48 262.5,40.53 264.0,41.14 265.5,38.5 267.0,32.92 268.5,28.74 270.0,28.43 271.5,29.59 273.0,28.92 274.5,25.9 276.0,21.52 277.5,16.83 279.0,14.02 280.5,15.63 282.0,20.5 283.5,23.6 285.0,22.6 286.5,21.54 288.0,24.86 289.5,30.32 291.0,32.27 292.5,30.2 294.0,29.07 295.5,31.54 297.0,35.11 298.5,37.66 300.0,41.04 301.5,46.61 303.0,51.21 304.5,50.59 306.0,44.61 307.5,36.46 309.0,28.94 310.5,23.88 312.0,22.87 313.5,25.09 315.0,26.39 316.5,24.04 318.0,21.24 319.5,22.91 321.0,28.07 322.5,30.82 324.0,29.01 325.5,26.87 327.0,27.91 328.5,29.71 330.0,28.79 331.5,26.31 333.0,25.45 334.5,25.64 336.0,23.91 337.5,20.39 339.0,18.64 340.5,20.87 342.0,26.15 343.5,32.66 345.0,38.4 346.5,40.28 348.0,36.62 349.5,31.03 351.0,29.68 352.5,33.65 354.0,37.66 355.5,38.1 357.0,37.92 358.5,40.91 360.0,44.96 361.5,45.21 363.0,41.39 364.5,37.28 366.0,34.08 367.5,29.31 369.0,22.34 370.5,16.54 372.0,14.74 373.5,15.93 375.0,17.69 376.5,18.91 378.0,18.93 379.5,17.37 381.0,16.6 382.5,20.83 384.0,30.04 385.5,37.96 387.0,39.21 388.5,35.94 390.0,33.88 391.5,33.9 393.0,32.42 394.5,28.89 396.0,27.41 397.5,30.13 399.0,33.84 400.5,35.27 402.0,35.62 403.5,37.31 405.0,39.4 406.5,39.18 408.0,36.19 409.5,31.98 411.0,27.87 412.5,25.56 414.0,27.65 415.5,34.0 417.0,39.2 418.5,37.94 420.0,32.04 421.5,28.04 423.0,28.18 424.5,28.28 426.0,25.33 427.5,21.93 429.0,21.02 430.5,20.65 432.0,17.68 433.5,13.66 435.0,12.88 436.5,16.2 438.0,20.78 439.5,24.85 441.0,29.11 442.5,34.02 444.0,38.94 445.5,43.93 447.0,48.67 448.5,50.0 450.0,44.74 451.5,35.58 453.0,30.0 454.5,31.43 456.0,35.39 457.5,36.4 459.0,35.06 460.5,34.78 462.0,34.88 463.5,32.03 465.0,26.75 466.5,23.44 468.0,23.9 469.5,25.18 471.0,24.57 472.5,23.08 474.0,22.66 475.5,23.47 477.0,25.21 478.5,27.93 480.0,30.05 481.5,28.9 483.0,25.32 484.5,24.42 486.0,28.74 487.5,33.52 489.0,32.56 490.5,26.63 492.0,21.73 493.5,20.66 495.0,21.13 496.5,22.08 498.0,26.27 499.5,34.79 501.0,43.46 502.5,47.6 504.0,47.3 505.5,45.62 507.0,43.9 508.5,41.82 510.0,39.56 511.5,37.05 513.0,32.96 514.5,27.56 516.0,24.54 517.5,26.47 519.0,29.66 520.5,27.99 522.0,21.48 523.5,16.41 525.0,16.53 526.5,18.89 528.0,19.87 529.5,20.61 531.0,23.4 532.5,26.3 534.0,25.95 535.5,23.38 537.0,23.04 538.5,26.93 540.0,32.98 541.5,38.62 543.0,42.44 544.5,43.03 546.0,39.95 547.5,35.97 549.0,34.5 550.5,34.39 552.0,31.26 553.5,25.04 555.0,21.76 556.5,25.62 558.0,33.04 559.5,37.95 561.0,39.48 562.5,40.53 564.0,41.14 565.5,38.5 567.0,32.92 568.5,28.74 570.0,28.43 571.5,29.59 573.0,28.92 574.5,25.9 576.0,21.52 577.5,16.83 579.0,14.02 580.5,15.63 582.0,20.5 583.5,23.6 585.0,22.6 586.5,21.54 588.0,24.86 589.5,30.32 591.0,32.27 592.5,30.2 594.0,29.07 595.5,31.54 597.0,35.11 598.5,37.66 600.0,41.04";

/**
 * Live conversation waveform.
 * The wave itself is constant-amplitude and scrolls seamlessly (it is built from
 * integer harmonics over a 300-unit period, so x=0 and x=300 match exactly).
 * A static lens-shaped mask gives it the centred envelope — loud in the middle,
 * tapering to the baseline at both edges — so the shape stays put while the
 * audio moves through it.
 */
function AgentWaveform({ active }: { active: boolean }) {
  return (
    <div className={`shield-waveform ${active ? "is-live" : ""}`} aria-hidden="true">
      <span className="shield-waveform-base" />
      <svg viewBox="0 0 300 60" preserveAspectRatio="none">
        <defs>
          <linearGradient id="agentWave" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="300" y2="0" spreadMethod="repeat">
            <stop offset="0%" stopColor="#ff5b3a" />
            <stop offset="16%" stopColor="#ffb020" />
            <stop offset="33%" stopColor="#ffe046" />
            <stop offset="50%" stopColor="#4fd06a" />
            <stop offset="66%" stopColor="#35b8ff" />
            <stop offset="83%" stopColor="#7c5cff" />
            <stop offset="100%" stopColor="#ff5b3a" />
          </linearGradient>
          <mask id="agentEnvelope" maskUnits="userSpaceOnUse" maskContentUnits="userSpaceOnUse" x="0" y="0" width="300" height="60">
            <path
              d="M0,29.4 C58,12 104,3 150,3 C196,3 242,12 300,29.4 L300,30.6 C242,48 196,57 150,57 C104,57 58,48 0,30.6 Z"
              fill="#fff"
            />
          </mask>
        </defs>
        <g mask="url(#agentEnvelope)">
          <polyline
            className="shield-waveline"
            points={WAVE_POINTS}
            fill="none"
            stroke="url(#agentWave)"
            strokeWidth="1.9"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>
      </svg>
    </div>
  );
}

function useElapsed() {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const id = window.setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(id);
  }, []);
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

export type VoiceState = "idle" | "recording" | "transcribing" | "synthesizing" | "playing";

export function ShieldCopilotScreen({ messages, thinking = false, input, placeholder, sendLabel, onInput, onReply, onBack, voiceState = "idle", voiceError, voiceStatus, onToggleRecording, onPlayAnswer }: { messages: CopilotMessage[]; thinking?: boolean; input: string; placeholder: string; sendLabel: string; onInput: (value: string) => void; onReply: (value: string) => void; onBack: () => void; voiceState?: VoiceState; voiceError?: string | null; voiceStatus?: string | null; onToggleRecording?: () => void; onPlayAnswer?: () => void }) {
  const t = useT();
  const elapsed = useElapsed();
  const lastAssistant = [...messages].reverse().find((message) => message.role === "assistant");
  const recording = voiceState === "recording";
  const voiceBusy = voiceState === "transcribing" || voiceState === "synthesizing";

  return (
    <div className="shield-screen shield-agent-screen">
      <div className="shield-agent-topbar">
        <label className="shield-agent-search">
          <Search size={18} strokeWidth={2.1} />
          <input aria-label="Search your support topics" placeholder={t("copilot.search")} />
          <span aria-hidden="true"><SlidersHorizontal size={17} strokeWidth={2.1} /></span>
        </label>
        <button className="shield-agent-call" aria-label="Request an officer callback"><PhoneCall size={20} strokeWidth={2} /></button>
      </div>

      <section className="shield-agent-heading">
        <h1>{t("copilot.heading")}</h1>
        <p>{t("copilot.sub")}</p>
      </section>

      <div className="shield-agent-map" aria-hidden="true">
        <span className="shield-map-contour c-one" /><span className="shield-map-contour c-two" /><span className="shield-map-contour c-three" />
        <span className="shield-agent-pin p-one"><i /></span>
        <span className="shield-agent-pin p-two"><i /></span>
        <span className="shield-agent-pin p-three"><i /></span>
      </div>

      <section className="shield-agent-sheet">
        <span className="shield-sheet-handle" aria-hidden="true" />
        <p className="shield-agent-connect">{thinking ? t("copilot.speaking") : t("copilot.connected")}</p>

        <div className="shield-agent-parties">
          <span className="shield-party is-you" aria-hidden="true"><UserRound size={26} strokeWidth={1.8} /></span>
          <div className="shield-party-status">
            <strong>{t("copilot.update")}</strong>
            <small>{t("copilot.connectedSub")}</small>
            <b>{elapsed}</b>
          </div>
          <span className="shield-party is-agent" aria-hidden="true"><Bot size={26} strokeWidth={1.8} /></span>
        </div>

        <AgentWaveform active={thinking} />

        <div className="shield-agent-transcript" aria-live="polite">
          {lastAssistant && !thinking && <p>{lastAssistant.text}</p>}
          {thinking && <p className="is-muted">{t("copilot.thinking")}</p>}
          {voiceStatus && <p className="is-voice-status">{voiceStatus}</p>}
          {voiceError && <p className="is-voice-error" role="alert">{voiceError}</p>}
        </div>

        <div className="shield-quick-prompts">
          <button onClick={() => onReply("Why is my status red?")}>{t("copilot.prompt.why")}</button>
          <button onClick={() => onReply("What should I do today?")}>{t("copilot.prompt.what")}</button>
          <button onClick={() => onReply("Compare nearby markets")}>{t("copilot.prompt.market")}</button>
        </div>

        <div className="shield-agent-emergency">
          <span>{t("copilot.urgent")}</span>
          <button onClick={() => onReply("I need an officer to call me")}>{t("copilot.callOfficer")}</button>
        </div>
      </section>

      <div className="shield-chat-composer">
        <button className="shield-composer-speak" aria-label={voiceState === "playing" ? "Stop playback" : "Play the answer aloud"} disabled={!lastAssistant || voiceBusy} onClick={onPlayAnswer}>
          {voiceState === "playing" ? <VolumeX size={19} strokeWidth={2} /> : <Volume2 size={19} strokeWidth={2} />}
        </button>
        <label className="shield-composer-field">
          <input value={input} onChange={(event) => onInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") onReply(input); }} placeholder={placeholder} aria-label={placeholder} />
          <button className={`shield-composer-mic${recording ? " is-recording" : ""}`} aria-label={recording ? "Stop recording" : "Record a voice question"} disabled={voiceBusy || thinking} onClick={onToggleRecording}>
            {recording ? <Square size={15} strokeWidth={2.4} fill="currentColor" /> : <Mic size={17} strokeWidth={2.2} />}
          </button>
          <button aria-label={sendLabel} disabled={!input.trim()} onClick={() => onReply(input)}><AudioLines size={18} strokeWidth={2.2} /></button>
        </label>
        <button className="shield-composer-close" aria-label="Close copilot" onClick={onBack}><X size={20} strokeWidth={2.2} /></button>
      </div>
    </div>
  );
}

export function ShieldPrivacyScreen({ consent, privacyText, onUpdate, onReviewSetup, onBack }: { consent: ConsentState; privacyText: string; onUpdate: (key: keyof ConsentState, value: boolean) => void; onReviewSetup: () => void; onBack: () => void }) {
  const t = useT();
  return (
    <div className="shield-screen">
      <InnerHeader title={t("menu.privacy")} subtitle={t("menu.privacy.subtitle")} onBack={onBack} />
      <section className="shield-privacy-hero"><span><LockKeyhole size={25} /></span><h1>Your information, your choice</h1><p>{privacyText}</p></section>
      <section className="shield-consent-card">
        <ConsentToggle label={t("onboarding.privacy.storage")} description={t("onboarding.privacy.storageBody")} value={consent.storage} onChange={(value) => onUpdate("storage", value)} />
        <ConsentToggle label={t("onboarding.privacy.contact")} description={t("onboarding.privacy.contactBody")} value={consent.contact} onChange={(value) => onUpdate("contact", value)} />
        <ConsentToggle label={t("onboarding.privacy.email")} description={t("onboarding.privacy.emailBody")} value={consent.email_alerts} onChange={(value) => onUpdate("email_alerts", value)} />
        <ConsentToggle label={t("onboarding.privacy.analytics")} description={t("onboarding.privacy.analyticsBody")} value={consent.analytics} onChange={(value) => onUpdate("analytics", value)} />
        <ConsentToggle label={t("onboarding.support.dueTitle")} description={t("onboarding.support.dueBody")} value={consent.due_window} onChange={(value) => onUpdate("due_window", value)} />
      </section>
      <button className="shield-secondary-cta" onClick={onReviewSetup}>Review my setup <ChevronRight size={18} /></button>
    </div>
  );
}

export function ShieldMoreScreen({ locale, localeName, onLocale, onMarkets, onPrivacy, onAsk, onSignOut }: { locale: string; localeName: string; onLocale: (locale: "en" | "hi" | "mr") => void; onMarkets: () => void; onPrivacy: () => void; onAsk: () => void; onSignOut: () => void }) {
  const t = useT();
  return (
    <div className="shield-screen">
      <section className="shield-profile-hero">
        <span className="shield-profile-avatar"><UserRound size={35} /></span>
        <h1>{t("profile.title")}</h1><p>Dindori · Cotton · Kharif</p>
        <div><span><b>74</b><small>{t("profile.score")}</small></span><i /><span><b>86%</b><small>{t("profile.confidence")}</small></span></div>
      </section>
      <section className="shield-menu-card">
        <button onClick={onMarkets}><span><Store size={19} /></span><span><strong>{t("menu.markets")}</strong><small>{t("menu.markets.sub2")}</small></span><ChevronRight size={18} /></button>
        <button onClick={onAsk}><span><Headphones size={19} /></span><span><strong>{t("menu.copilot")}</strong><small>{t("menu.copilot.sub")}</small></span><ChevronRight size={18} /></button>
        <button onClick={onPrivacy}><span><LockKeyhole size={19} /></span><span><strong>{t("menu.privacy")}</strong><small>{t("menu.privacy.sub")}</small></span><ChevronRight size={18} /></button>
      </section>
      <label className="shield-language-row"><span><Languages size={19} /></span><span><strong>{t("language.select")}</strong><small>{localeName}</small></span><select aria-label="App language" value={locale} onChange={(event) => onLocale(event.target.value as "en" | "hi" | "mr")}><option value="mr">ਪੰਜਾਬੀ</option><option value="hi">हिंदी</option><option value="en">English</option></select></label>
      <div className="shield-safety-note"><ShieldCheck size={18} /><span><strong>{t("support.network")}</strong><small>{t("support.networkSub")}</small></span></div>
      <button className="shield-secondary-cta" onClick={onSignOut}><LogOut size={18} /> Sign out</button>
    </div>
  );
}
