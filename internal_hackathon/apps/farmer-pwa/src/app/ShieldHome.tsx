import { useState } from "react";
import {
  BellRing,
  Bot,
  CircleAlert,
  CloudRain,
  Filter,
  Home,
  IndianRupee,
  MapPin,
  MessageCircleMore,
  ShieldCheck,
  Sparkles,
  Sprout,
  UserRound,
} from "lucide-react";
import type { Band, RiskEvent } from "ui-kit";

type FarmerScreen = "home" | "why" | "action" | "copilot" | "mandi" | "settings" | "more";

interface ShieldHomeProps {
  event: RiskEvent;
  updatedLabel: string;
  onOpenWhy: () => void;
  onOpenAction: () => void;
  onOpenCopilot: () => void;
  onOpenMandi: () => void;
}

const STATUS_COPY: Record<Band, { label: string; className: string; short: string }> = {
  green: { label: "Looking steady", className: "is-steady", short: "Stable" },
  amber: { label: "Keep watch", className: "is-watch", short: "Watch" },
  red: { label: "Support needed", className: "is-urgent", short: "Priority" },
};

export function ShieldHome({ event, updatedLabel, onOpenWhy, onOpenAction, onOpenCopilot, onOpenMandi }: ShieldHomeProps) {
  const [category, setCategory] = useState("All");
  const status = STATUS_COPY[event.band];

  return (
    <div className="shield-home">
      <header className="shield-brandbar">
        <div className="shield-wordmark">
          <span className="shield-logo" aria-hidden="true"><ShieldCheck size={22} strokeWidth={1.9} /></span>
          <span><strong>KISANSETU</strong><small>Farmer support network</small></span>
        </div>
        <button className="shield-profile" aria-label="Open farmer profile">
          <UserRound size={20} strokeWidth={1.8} />
          <span className="shield-profile-dot" />
        </button>
      </header>

      <section className="shield-intro" aria-labelledby="nearby-heading">
        <h1 id="nearby-heading">What’s happening nearby? <em>Get crop support early.</em></h1>
        <p><MapPin size={14} /> Dindori, Nashik · {updatedLabel}</p>
      </section>

      <button className="shield-live-strip" onClick={onOpenWhy}>
        <span className="shield-live-thumb" aria-hidden="true" />
        <span className="shield-live-copy"><strong>Cotton support alert</strong><small>{status.label} · live update</small></span>
        <span className={`shield-live-badge ${status.className}`}><span /> Live</span>
      </button>

      <div className="shield-filter-row" aria-label="Filter farmer updates">
        <span className="shield-filter-icon" aria-hidden="true"><Filter size={18} /></span>
        {["All", "Weather", "Crop", "Market", "Support"].map((item) => (
          <button key={item} className={`shield-chip ${category === item ? "active" : ""}`} aria-pressed={category === item} onClick={() => setCategory(item)}>{item}</button>
        ))}
      </div>

      <section className="shield-alert-section" aria-labelledby="alerts-heading">
        <div className="shield-section-heading"><div><span>NEARBY UPDATE</span><h2 id="alerts-heading">Your field signals</h2></div><button onClick={onOpenWhy}>See details</button></div>
        <div className="shield-alert-rail">
          <button className="shield-alert-card shield-crop-alert" onClick={onOpenWhy}>
            <span className="shield-card-top"><span className="shield-score-pill"><CircleAlert size={14} /> {event.score}/100</span><span className="shield-card-live"><span /> Live</span></span>
            <span className="shield-card-copy"><strong>Cotton stress alert<br />in Dindori</strong><small>Rainfall, crop and market signals need a same-day review.</small></span>
            <span className="shield-card-footer"><span><CloudRain size={15} /> Rain −28%</span><span><Sprout size={15} /> Crop stress</span><span><BellRing size={15} /> {Math.round(event.confidence * 100)}%</span></span>
          </button>
          <button className="shield-alert-card shield-market-alert" onClick={onOpenMandi}>
            <span className="shield-card-top"><span className="shield-score-pill"><IndianRupee size={14} /> Market</span><span className="shield-card-live is-blue">Updated</span></span>
            <span className="shield-market-orb" aria-hidden="true"><IndianRupee size={34} /></span>
            <span className="shield-card-copy"><strong>Compare before<br />you sell</strong><small>Lasalgaon is currently ₹360 above Dindori.</small></span>
          </button>
        </div>
      </section>

      <section className="shield-next-card">
        <span className="shield-next-icon"><Sparkles size={20} /></span>
        <span><small>RECOMMENDED TODAY</small><strong>Share crop condition with your officer</strong><p>Your copilot can explain the alert in simple language.</p></span>
        <button onClick={onOpenCopilot} aria-label="Ask support copilot"><Bot size={20} /></button>
      </section>

      <button className="shield-plan-button" onClick={onOpenAction}><span><span className="shield-plan-check">✓</span><span><strong>View today’s action plan</strong><small>3 safe, reviewed steps</small></span></span><span aria-hidden="true">→</span></button>
    </div>
  );
}

export function ShieldDock({ screen, labels, onNavigate }: { screen: FarmerScreen; labels: { home: string; status: string; ask: string; more: string }; onNavigate: (screen: FarmerScreen) => void }) {
  const statusActive = screen === "why" || screen === "action" || screen === "mandi";
  const moreActive = screen === "more" || screen === "settings";
  return (
    <nav className="shield-dock" aria-label="Farmer navigation">
      <button className={screen === "home" ? "active" : ""} onClick={() => onNavigate("home")}><span><Home size={20} /></span><small>{labels.home}</small></button>
      <button className={statusActive ? "active" : ""} onClick={() => onNavigate("why")}><span><CircleAlert size={20} /></span><small>{labels.status}</small></button>
      <button className={screen === "copilot" ? "active" : ""} onClick={() => onNavigate("copilot")}><span><MessageCircleMore size={20} /></span><small>{labels.ask}</small></button>
      <button className={moreActive ? "active" : ""} onClick={() => onNavigate("more")}><span><Sprout size={20} /></span><small>{labels.more}</small></button>
    </nav>
  );
}
