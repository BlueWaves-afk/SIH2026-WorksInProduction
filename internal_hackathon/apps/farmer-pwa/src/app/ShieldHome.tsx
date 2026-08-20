import { useState } from "react";
import {
  Bot,
  CircleAlert,
  Globe,
  MapPin,
  MessageCircleMore,
  SlidersHorizontal,
  Sparkles,
  Sprout,
  ThumbsUp,
  UserRound,
} from "lucide-react";
import type { Band, RiskEvent } from "ui-kit";
import { useT } from "../i18n";

type FarmerScreen = "home" | "alerts" | "why" | "action" | "copilot" | "mandi" | "settings" | "more";

interface ShieldHomeProps {
  event: RiskEvent;
  updatedLabel: string;
  onOpenWhy: () => void;
  onOpenAction: () => void;
  onOpenCopilot: () => void;
  onOpenMandi: () => void;
}

const BAND_CLASS: Record<Band, string> = { green: "is-steady", amber: "is-watch", red: "is-urgent" };
const FILTERS_ROW_ONE = ["filter.all", "filter.weather", "filter.crop", "filter.market"];
const FILTERS_ROW_TWO = ["filter.water", "filter.pest", "filter.scheme", "filter.advisory"];

export function ShieldHome({ event, updatedLabel, onOpenWhy, onOpenAction, onOpenCopilot, onOpenMandi }: ShieldHomeProps) {
  const t = useT();
  const [category, setCategory] = useState("filter.all");

  return (
    <div className="shield-home">
      <header className="shield-brandbar">
        <div className="shield-wordmark">
          <span className="shield-logo" aria-hidden="true" />
          <span>
            <strong>{t("app.name")}</strong>
            <small>{t("app.tagline")}</small>
          </span>
        </div>
        <button className="shield-profile" aria-label="Open farmer profile">
          <UserRound size={21} strokeWidth={1.8} />
          <span className="shield-profile-dot" />
        </button>
      </header>

      <section className="shield-intro">
        <h1>{t("home.headline")} <em>{t("home.headline.accent")}</em></h1>
      </section>

      <button className="shield-live-strip" onClick={onOpenWhy}>
        <span className="shield-live-thumb" aria-hidden="true" />
        <span className="shield-live-copy">
          <strong>{t("home.live.title")}</strong>
          <small>{t(`band.${event.band}`)}</small>
        </span>
        <span className={`shield-live-badge ${BAND_CLASS[event.band]}`}><span /> {t("home.live.badge")}</span>
      </button>

      <div className="shield-filter-block" aria-label="Filter farmer updates">
        <div className="shield-filter-row">
          <span className="shield-filter-icon" aria-hidden="true"><SlidersHorizontal size={19} strokeWidth={2} /></span>
          {FILTERS_ROW_ONE.map((item) => (
            <button key={item} className={`shield-chip ${category === item ? "active" : ""}`} aria-pressed={category === item} onClick={() => setCategory(item)}>{t(item)}</button>
          ))}
        </div>
        <div className="shield-filter-row is-offset">
          {FILTERS_ROW_TWO.map((item) => (
            <button key={item} className={`shield-chip ${category === item ? "active" : ""}`} aria-pressed={category === item} onClick={() => setCategory(item)}>{t(item)}</button>
          ))}
        </div>
      </div>

      <section className="shield-alert-section" aria-label="Field signal alerts">
        <div className="shield-alert-rail">
          <button className="shield-alert-card shield-crop-alert" onClick={onOpenWhy}>
            <span className="shield-tile-haze" aria-hidden="true"><i /><i /><i /><i /></span>
            <span className="shield-card-copy">
              <strong>Cotton Stress Alert<br />In Dindori, Nashik!</strong>
            </span>
            <span className="shield-card-footer">
              <span className="shield-face-stack" aria-hidden="true"><i /><i /><i /></span>
              <span className="shield-stat">{event.score}/100</span>
              <span className="shield-stat"><ThumbsUp size={13} strokeWidth={2.2} /> {Math.round(event.confidence * 100)}%</span>
              <span className="shield-stat"><MessageCircleMore size={13} strokeWidth={2.2} /> 3</span>
            </span>
          </button>
          <button className="shield-alert-card shield-market-alert" onClick={onOpenMandi}>
            <span className="shield-tile-haze" aria-hidden="true"><i /><i /><i /><i /></span>
            <span className="shield-card-copy">
              <strong>Market Price Drop<br />Compare Before Selling!</strong>
            </span>
            <span className="shield-card-footer">
              <span className="shield-face-stack" aria-hidden="true"><i /><i /><i /></span>
              <span className="shield-stat">₹360 gap</span>
              <span className="shield-stat"><ThumbsUp size={13} strokeWidth={2.2} /> 4</span>
              <span className="shield-stat"><MapPin size={13} strokeWidth={2.2} /> 18km</span>
            </span>
          </button>
        </div>
      </section>

      <section className="shield-next-card">
        <span className="shield-next-icon"><Sparkles size={20} /></span>
        <span><small>{t("home.recommended.kicker")}</small><strong>{t("home.recommended.title")}</strong><p>{t("home.recommended.body")}</p></span>
        <button onClick={onOpenCopilot} aria-label="Ask support copilot"><Bot size={20} /></button>
      </section>

      <button className="shield-plan-button" onClick={onOpenAction}><span><span className="shield-plan-check">✓</span><span><strong>{t("home.plan.title")}</strong><small>{t("home.plan.sub")} · {updatedLabel}</small></span></span><span aria-hidden="true">→</span></button>
    </div>
  );
}

export function ShieldDock({ screen, labels, onNavigate }: { screen: FarmerScreen; labels: { home: string; status: string; ask: string; more: string }; onNavigate: (screen: FarmerScreen) => void }) {
  const statusActive = screen === "alerts" || screen === "why" || screen === "action";
  const moreActive = screen === "more" || screen === "settings";
  return (
    <nav className="shield-dock" aria-label="Farmer navigation">
      <button className={screen === "home" ? "active" : ""} aria-label={labels.home} onClick={() => onNavigate("home")}><span><Globe size={21} strokeWidth={2} /></span></button>
      <button className={screen === "mandi" ? "active" : ""} aria-label="Nearby markets" onClick={() => onNavigate("mandi")}><span><MapPin size={21} strokeWidth={2} /></span></button>
      <button className={statusActive ? "active" : ""} aria-label={labels.status} onClick={() => onNavigate("alerts")}><span><CircleAlert size={21} strokeWidth={2} /></span></button>
      <button className={screen === "copilot" ? "active" : ""} aria-label={labels.ask} onClick={() => onNavigate("copilot")}><span><MessageCircleMore size={21} strokeWidth={2} /></span></button>
      <button className={moreActive ? "active" : ""} aria-label={labels.more} onClick={() => onNavigate("more")}><span><Sprout size={21} strokeWidth={2} /></span></button>
    </nav>
  );
}
