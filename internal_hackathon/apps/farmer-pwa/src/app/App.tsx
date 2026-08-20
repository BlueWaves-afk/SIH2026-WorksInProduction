import { useEffect, useMemo, useState } from "react";
import {
  ActionCardView,
  Button,
  ConsentToggle,
  IconPicker,
  OfflineBanner,
  ScoreBreakdown,
  SeasonWheel,
  StaleBadge,
  TrafficLightDisc,
  type ConsentState,
} from "ui-kit";
import "ui-kit/styles.css";
import { loadFarmerStatus, submitFarmerProfile, type FarmerStatus } from "../api/client";
import { demoActionCard, demoMandis, demoRiskEvent } from "../demo";

type Screen = "home" | "why" | "action" | "mandi" | "settings";

const copy = {
  en: { name: "English", welcome: "Farmer support", home: "Your current support status", why: "Why this status", action: "What you can do next", mandi: "Compare nearby mandis", settings: "Privacy and settings" },
  hi: { name: "हिंदी", welcome: "किसान सहायता", home: "आपकी सहायता स्थिति", why: "यह स्थिति क्यों है", action: "अब आप क्या कर सकते हैं", mandi: "पास की मंडियों की तुलना", settings: "गोपनीयता और सेटिंग्स" },
  mr: { name: "मराठी", welcome: "शेतकरी मदत", home: "तुमची मदत स्थिती", why: "ही स्थिती का आहे", action: "आता तुम्ही काय करू शकता", mandi: "जवळच्या बाजारांची तुलना", settings: "गोपनीयता आणि सेटिंग्ज" },
} as const;

const crops = [
  { value: "cotton", label: "Cotton", icon: "🌱" },
  { value: "soybean", label: "Soybean", icon: "🌿" },
  { value: "groundnut", label: "Groundnut", icon: "🥜" },
] as const;

const irrigation = [
  { value: "rainfed", label: "Rain-fed", icon: "🌧️" },
  { value: "well", label: "Well", icon: "💧" },
  { value: "canal", label: "Canal", icon: "🛶" },
] as const;

function initialConsent(): ConsentState {
  return { storage: false, contact: false, analytics: false, due_window: false };
}

export function App() {
  const [locale, setLocale] = useState<keyof typeof copy>("mr");
  const [screen, setScreen] = useState<Screen>("home");
  const [onboarded, setOnboarded] = useState(() => window.localStorage.getItem("sih-demo-onboarded") === "true");
  const [crop, setCrop] = useState("cotton");
  const [season, setSeason] = useState<"kharif" | "rabi" | "zaid">("kharif");
  const [irrigationType, setIrrigationType] = useState("rainfed");
  const [consent, setConsent] = useState<ConsentState>(initialConsent);
  const [status, setStatus] = useState<FarmerStatus>({ risk_event: demoRiskEvent, action_card: demoActionCard, mandis: demoMandis, cached_at: new Date().toISOString(), source: "demo-fixture" });
  const [online, setOnline] = useState(() => navigator.onLine);
  const [submitting, setSubmitting] = useState(false);
  const t = copy[locale];

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    if (onboarded) void loadFarmerStatus().then(setStatus);
    return () => { window.removeEventListener("online", onOnline); window.removeEventListener("offline", onOffline); };
  }, [onboarded]);

  const stale = !online || Date.now() - new Date(status.cached_at).getTime() > 24 * 60 * 60 * 1000;
  const updateConsent = (key: keyof ConsentState) => (value: boolean) => setConsent((current) => ({ ...current, [key]: value, ...(key === "storage" && !value ? { contact: false, analytics: false, due_window: false } : {}) }));

  async function completeOnboarding() {
    if (!consent.storage) return;
    setSubmitting(true);
    try {
      await submitFarmerProfile({ locale, crop, season, irrigation: irrigationType, consent_flags: consent });
    } catch {
      // The API is still being implemented by M1. The demo remains honest and uses a labelled fixture.
    } finally {
      window.localStorage.setItem("sih-demo-onboarded", "true");
      setOnboarded(true);
      setSubmitting(false);
    }
  }

  if (!onboarded) {
    return (
      <main className="app-shell"><div className="app-container" style={{ maxWidth: 700 }}>
        <header className="app-header"><div><p className="eyebrow">SIH PS-02 · Farmer support radar</p><h1>{t.welcome}</h1><p className="subtitle">A 60-second setup. Tap choices instead of typing. Your support score is never a credit or loan-default score.</p></div><span className="band-chip green">Offline-ready</span></header>
        <div className="surface panel stack">
          <IconPicker label="Choose your language / भाषा / भाषा निवडा" options={(Object.entries(copy).map(([value, item]) => ({ value: value as keyof typeof copy, label: item.name, icon: value === "mr" ? "अ" : value === "hi" ? "आ" : "A" })))} value={locale} onChange={setLocale} />
          <IconPicker label="What do you grow?" options={[...crops]} value={crop} onChange={setCrop} />
          <SeasonWheel value={season} onChange={setSeason} />
          <IconPicker label="How do you irrigate?" options={[...irrigation]} value={irrigationType} onChange={setIrrigationType} />
          <div><h2>Choose what we may use</h2><p className="muted small">These controls are off by default. You can change them later. We only send an officer contact when you opt in.</p>
            <ConsentToggle label="Save my support information" description="Needed to show your status again on this device." value={consent.storage} onChange={updateConsent("storage")} />
            <ConsentToggle label="Allow officer contact" description="Lets an extension officer call or refer your case." value={consent.contact} onChange={updateConsent("contact")} />
            <ConsentToggle label="Include me in anonymous trends" description="Only group results are used; no individual dashboard." value={consent.analytics} onChange={updateConsent("analytics")} />
            <ConsentToggle label="Share a coarse repayment window" description="Optional timing only; never a lender, account or credit score." value={consent.due_window} onChange={updateConsent("due_window")} />
          </div>
          <div className="notice">The app can display your last saved result without a network. It never recalculates a score on your phone.</div>
          <Button onClick={() => void completeOnboarding()} disabled={!consent.storage || submitting}>{submitting ? "Saving…" : "Show my support status"}</Button>
        </div>
      </div></main>
    );
  }

  const statusLabel = stale ? "Last saved status" : t.home;
  return (
    <main className="app-shell"><div className="app-container">
      <header className="app-header"><div><p className="eyebrow">SIH PS-02 · {status.risk_event.village_id}</p><h1>{t.welcome}</h1><p className="subtitle">{statusLabel} · {status.source === "api" ? "connected to platform" : "demo fixture while platform API is unavailable"}</p></div><div className="row"><label className="small muted" htmlFor="locale">Language</label><select id="locale" value={locale} onChange={(event) => setLocale(event.target.value as keyof typeof copy)}><option value="mr">मराठी</option><option value="hi">हिंदी</option><option value="en">English</option></select></div></header>
      <OfflineBanner online={online} cachedAt={status.cached_at} />
      <div className="tab-bar" role="tablist" aria-label="Farmer app sections">{(["home", "why", "action", "mandi", "settings"] as Screen[]).map((item) => <button key={item} className={`tab ${screen === item ? "active" : ""}`} onClick={() => setScreen(item)} role="tab" aria-selected={screen === item}>{item === "home" ? "Home" : item === "why" ? t.why : item === "action" ? t.action : item === "mandi" ? "Mandi" : "Settings"}</button>)}</div>
      <div className="grid" style={{ marginTop: 18 }}>
        {screen === "home" && <>
          <section className="surface panel status-card"><TrafficLightDisc band={status.risk_event.band} score={status.risk_event.score} /><div><div className="row"><h2>{t.home}</h2><span className="spacer" /><StaleBadge stale={stale} /></div><p className="subtitle">{status.risk_event.band === "red" ? "An agriculture officer should review this today." : "No urgent follow-up is currently needed."}</p><div className="case-meta"><span>Confidence {Math.round(status.risk_event.confidence * 100)}%</span><span>Valid until {new Date(status.risk_event.expires_at).toLocaleString()}</span></div><p className="footer-note">{status.risk_event.disclaimer}</p></div></section>
          <ScoreBreakdown event={status.risk_event} title={t.why} />
          {status.risk_event.band === "red" && <ActionCardView card={status.action_card} />}
        </>}
        {screen === "why" && <ScoreBreakdown event={status.risk_event} title={t.why} />}
        {screen === "action" && <ActionCardView card={status.action_card} />}
        {screen === "mandi" && <section className="surface panel"><p className="eyebrow">Decision support</p><h2>{t.mandi}</h2><p className="muted">Prices are shown as a comparison only. The officer or FPO confirms the next step.</p><div className="stack">{status.mandis.map((mandi) => <div className="check-row" key={mandi.mandi}><div><strong>{mandi.mandi}</strong><div className="muted small">{mandi.distance_km} km · verified {new Date(mandi.verified_at).toLocaleDateString()}</div></div><div style={{ textAlign: "right" }}><strong>₹{mandi.modal_price.toLocaleString("en-IN")}</strong><div className={mandi.change_pct < 0 ? "small" : "small muted"} style={{ color: mandi.change_pct < 0 ? "#b42318" : undefined }}>{mandi.change_pct}% seasonal change</div></div></div>)}</div></section>}
        {screen === "settings" && <section className="surface panel"><p className="eyebrow">M2 consent controls</p><h2>{t.settings}</h2><p className="muted">Changing consent updates the next platform request. This demo stores only a local completion flag and the last display status.</p><ConsentToggle label="Save my support information" description="Needed to show your status again on this device." value={consent.storage} onChange={updateConsent("storage")} /><ConsentToggle label="Allow officer contact" description="Lets an extension officer call or refer your case." value={consent.contact} onChange={updateConsent("contact")} /><ConsentToggle label="Include me in anonymous trends" description="Only group results are used." value={consent.analytics} onChange={updateConsent("analytics")} /><ConsentToggle label="Share a coarse repayment window" description="Optional timing only; no account or lender data." value={consent.due_window} onChange={updateConsent("due_window")} /><div className="row" style={{ marginTop: 16 }}><Button variant="secondary" onClick={() => { window.localStorage.removeItem("sih-demo-onboarded"); setOnboarded(false); }}>Review onboarding</Button><Button variant="ghost" onClick={() => setOnline(navigator.onLine)}>Refresh connection</Button></div></section>}
      </div>
      <p className="footer-note">M8 renders M1's RiskEvent and approved ActionCard. It does not compute bands, scores, confidence or case decisions.</p>
    </div></main>
  );
}
