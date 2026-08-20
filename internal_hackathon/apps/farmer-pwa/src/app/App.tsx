import { useEffect, useState } from "react";
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
  type CopilotMessage,
} from "ui-kit";
import "ui-kit/styles.css";
import { loadFarmerStatus, submitFarmerProfile, type FarmerStatus } from "../api/client";
import { demoActionCard, demoMandis, demoRiskEvent } from "../demo";

type Screen = "home" | "why" | "action" | "copilot" | "mandi" | "settings" | "more";
type Locale = "en" | "hi" | "mr";

const copy: Record<Locale, {
  name: string; welcome: string; home: string; why: string; action: string; ask: string; mandi: string; settings: string;
  statusRed: string; statusGreen: string; updated: string; offline: string; assistantTitle: string; assistantBody: string;
  askPlaceholder: string; send: string; more: string; privacy: string;
}> = {
  en: { name: "English", welcome: "Farmer support", home: "Your support status", why: "Why this status", action: "Next steps", ask: "Ask support", mandi: "Nearby markets", settings: "Privacy", statusRed: "An agriculture officer should review this today.", statusGreen: "No urgent follow-up is currently needed.", updated: "Updated just now", offline: "Last saved status", assistantTitle: "Ask about your status", assistantBody: "Get a simple explanation or find the next safe step.", askPlaceholder: "Ask a question…", send: "Send", more: "More", privacy: "Your choices are yours to change." },
  hi: { name: "हिंदी", welcome: "किसान सहायता", home: "आपकी सहायता स्थिति", why: "यह स्थिति क्यों है", action: "अगले कदम", ask: "सहायता से पूछें", mandi: "पास की मंडियां", settings: "गोपनीयता", statusRed: "कृषि अधिकारी को आज इस मामले की समीक्षा करनी चाहिए।", statusGreen: "अभी तत्काल सहायता की जरूरत नहीं है।", updated: "अभी अपडेट किया गया", offline: "अंतिम सुरक्षित स्थिति", assistantTitle: "अपनी स्थिति के बारे में पूछें", assistantBody: "सरल भाषा में कारण और अगला सुरक्षित कदम जानें।", askPlaceholder: "सवाल लिखें…", send: "भेजें", more: "और", privacy: "आप अपनी पसंद कभी भी बदल सकते हैं।" },
  mr: { name: "मराठी", welcome: "शेतकरी मदत", home: "तुमची मदत स्थिती", why: "ही स्थिती का आहे", action: "पुढची पावले", ask: "मदतीला विचारा", mandi: "जवळचे बाजार", settings: "गोपनीयता", statusRed: "कृषी अधिकाऱ्याने आज या प्रकरणाची पाहणी करावी.", statusGreen: "सध्या तातडीच्या मदतीची गरज नाही.", updated: "आत्ताच अपडेट", offline: "शेवटची जतन केलेली स्थिती", assistantTitle: "तुमच्या स्थितीबद्दल विचारा", assistantBody: "सोप्या भाषेत कारण आणि पुढचे सुरक्षित पाऊल जाणून घ्या.", askPlaceholder: "प्रश्न विचारा…", send: "पाठवा", more: "अधिक", privacy: "तुम्ही तुमची निवड कधीही बदलू शकता." },
};

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

function localizedActionCard(locale: Locale) {
  if (locale === "mr") return demoActionCard;
  const hindi = locale === "hi";
  return {
    ...demoActionCard,
    locale,
    title: hindi ? "आज के सुरक्षित अगले कदम" : "Your safe next steps today",
    steps: hindi ? [
      { text: "अगले 48 घंटे में पानी और फसल की स्थिति कृषि अधिकारी को बताएं।" },
      { text: "दो नजदीकी बाजारों के भाव देखें और बेचने से पहले FPO से विकल्प पूछें।", deep_link: "mandi-compare" },
      { text: "अधिकारी या हेल्पलाइन से संपर्क मांगें; यह कर्ज का फैसला नहीं है।" },
    ] : [
      { text: "Share your water availability and crop condition with the agriculture officer today." },
      { text: "Compare two nearby market prices and ask your FPO about options before selling.", deep_link: "mandi-compare" },
      { text: "Request an officer or helpline callback; this is not a credit decision." },
    ],
  };
}

function starterMessages(locale: Locale): CopilotMessage[] {
  const greeting = locale === "mr" ? "नमस्कार. तुमची स्थिती समजावून सांगू आणि पुढचे सुरक्षित पाऊल शोधू शकतो." : locale === "hi" ? "नमस्ते। मैं आपकी स्थिति समझा सकता हूं और अगला सुरक्षित कदम ढूंढ सकता हूं।" : "Hello. I can explain your status and help find the next safe step.";
  return [{ id: "assistant-1", role: "assistant", text: greeting, created_at: new Date().toISOString() }];
}

export function App() {
  const [locale, setLocale] = useState<Locale>("mr");
  const [screen, setScreen] = useState<Screen>("home");
  const [onboarded, setOnboarded] = useState(() => window.localStorage.getItem("farmer-onboarded") === "true");
  const [crop, setCrop] = useState("cotton");
  const [season, setSeason] = useState<"kharif" | "rabi" | "zaid">("kharif");
  const [irrigationType, setIrrigationType] = useState("rainfed");
  const [consent, setConsent] = useState<ConsentState>(initialConsent);
  const [status, setStatus] = useState<FarmerStatus>({ risk_event: demoRiskEvent, action_card: demoActionCard, mandis: demoMandis, cached_at: new Date().toISOString(), source: "demo-fixture" });
  const [online, setOnline] = useState(() => navigator.onLine);
  const [submitting, setSubmitting] = useState(false);
  const [messages, setMessages] = useState<CopilotMessage[]>(() => starterMessages("mr"));
  const [copilotInput, setCopilotInput] = useState("");
  const t = copy[locale];

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    if (onboarded) void loadFarmerStatus().then(setStatus);
    return () => { window.removeEventListener("online", onOnline); window.removeEventListener("offline", onOffline); };
  }, [onboarded]);

  useEffect(() => setMessages(starterMessages(locale)), [locale]);

  const stale = !online || Date.now() - new Date(status.cached_at).getTime() > 24 * 60 * 60 * 1000;
  const actionCard = localizedActionCard(locale);
  const updateConsent = (key: keyof ConsentState) => (value: boolean) => setConsent((current) => ({ ...current, [key]: value, ...(key === "storage" && !value ? { contact: false, analytics: false, due_window: false } : {}) }));

  async function completeOnboarding() {
    if (!consent.storage) return;
    setSubmitting(true);
    try { await submitFarmerProfile({ locale, crop, season, irrigation: irrigationType, consent_flags: consent }); } catch { /* The status view remains available if the network is unavailable. */ }
    window.localStorage.setItem("farmer-onboarded", "true");
    setOnboarded(true);
    setSubmitting(false);
  }

  function replyTo(text: string) {
    const question = text.trim();
    if (!question) return;
    const lower = question.toLowerCase();
    const answer = lower.includes("why") || lower.includes("का") || lower.includes("का?")
      ? status.risk_event.contributors.slice(0, 2).map((driver) => driver.explanation).join(". ") + "."
      : lower.includes("market") || lower.includes("mandi") || lower.includes("बाजार")
        ? "I can compare nearby market prices. Open Nearby markets to review the latest available quotes before deciding."
        : "The safest next step is to share your crop condition with the agriculture officer. I can show the approved action plan or explain any driver.";
    setMessages((current) => [...current, { id: `farmer-${Date.now()}`, role: "farmer", text: question, created_at: new Date().toISOString() }, { id: `assistant-${Date.now() + 1}`, role: "assistant", text: answer, created_at: new Date().toISOString() }]);
    setCopilotInput("");
  }

  if (!onboarded) {
    return (
      <main className="app-shell farmer-shell"><div className="app-container">
        <header className="app-header"><div><div className="mobile-topline"><span className="location-pill"><span className="location-dot" /> Private setup</span><span className="band-chip green">Works offline</span></div><h1>{t.welcome}</h1><p className="subtitle">A few taps to get a clear support status. You never need to type a long form.</p></div></header>
        <div className="surface panel stack">
          <IconPicker label="Language / भाषा / भाषा निवडा" options={Object.entries(copy).map(([value, item]) => ({ value: value as Locale, label: item.name, icon: value === "mr" ? "अ" : value === "hi" ? "आ" : "A" }))} value={locale} onChange={setLocale} />
          <IconPicker label="What do you grow?" options={[...crops]} value={crop} onChange={setCrop} />
          <SeasonWheel value={season} onChange={setSeason} />
          <IconPicker label="How do you irrigate?" options={[...irrigation]} value={irrigationType} onChange={setIrrigationType} />
          <div><h2>Choose what we may use</h2><p className="muted small">These controls start off. You can change them later.</p>
            <ConsentToggle label="Save my support information" description="Needed to show your status again." value={consent.storage} onChange={updateConsent("storage")} />
            <ConsentToggle label="Allow officer contact" description="Lets an extension officer call or refer your case." value={consent.contact} onChange={updateConsent("contact")} />
            <ConsentToggle label="Include me in anonymous trends" description="Only group results are used." value={consent.analytics} onChange={updateConsent("analytics")} />
            <ConsentToggle label="Share a coarse repayment window" description="Timing only; never an account or credit record." value={consent.due_window} onChange={updateConsent("due_window")} />
          </div>
          <div className="notice">Your status is a support signal, not a credit, loan-default or insurance score.</div>
          <Button onClick={() => void completeOnboarding()} disabled={!consent.storage || submitting}>{submitting ? "Saving…" : "Continue"}</Button>
        </div>
      </div></main>
    );
  }

  const pageTitle = screen === "home" ? t.welcome : screen === "why" ? t.why : screen === "action" ? t.action : screen === "copilot" ? t.ask : screen === "mandi" ? t.mandi : screen === "settings" ? t.settings : t.more;
  return (
    <main className="app-shell farmer-shell"><div className="app-container">
      <header className="app-header"><div className="mobile-topline"><span className="location-pill"><span className="location-dot" /> {status.risk_event.village_id}</span><div className="row"><StaleBadge stale={stale} label={t.offline} /><select className="select-control" aria-label="Language" value={locale} onChange={(event) => setLocale(event.target.value as Locale)}><option value="mr">मराठी</option><option value="hi">हिंदी</option><option value="en">English</option></select></div></div><h1>{pageTitle}</h1><p className="subtitle">{online ? t.updated : t.offline}</p></header>
      <OfflineBanner online={online} cachedAt={status.cached_at} />
      <div className="grid" style={{ marginTop: 18 }}>
        {screen === "home" && <>
          <section className="surface panel status-card status-hero"><TrafficLightDisc band={status.risk_event.band} score={status.risk_event.score} /><div><div className="row"><span className="eyebrow" style={{ margin: 0 }}>Current status</span><span className="spacer" /><StaleBadge stale={stale} /></div><h2>{status.risk_event.band === "red" ? "Needs support" : "Looking steady"}</h2><p className="subtitle">{status.risk_event.band === "red" ? t.statusRed : t.statusGreen}</p><div className="case-meta"><span>Confidence {Math.round(status.risk_event.confidence * 100)}%</span><span>Valid until {new Date(status.risk_event.expires_at).toLocaleDateString()}</span></div></div></section>
          <section className="surface panel assistant-card"><div className="row"><span className="assistant-mark">✦</span><div><p className="eyebrow">Personal support</p><h2 style={{ marginBottom: 3 }}>{t.assistantTitle}</h2><p className="muted small" style={{ marginBottom: 0 }}>{t.assistantBody}</p></div></div><Button variant="secondary" onClick={() => setScreen("copilot")} style={{ marginTop: 16 }}>Open support chat <span aria-hidden="true">→</span></Button></section>
          <div className="quick-actions"><button className="quick-action" onClick={() => setScreen("why")}><span className="quick-action-icon">◌</span><strong>{t.why}</strong></button><button className="quick-action" onClick={() => setScreen("action")}><span className="quick-action-icon">✓</span><strong>{t.action}</strong></button><button className="quick-action" onClick={() => setScreen("mandi")}><span className="quick-action-icon">↗</span><strong>{t.mandi}</strong></button><button className="quick-action" onClick={() => setScreen("settings")}><span className="quick-action-icon">⋯</span><strong>{t.settings}</strong></button></div>
          <p className="footer-note">{status.risk_event.disclaimer}</p>
        </>}
        {screen === "why" && <ScoreBreakdown event={status.risk_event} title={t.why} />}
        {screen === "action" && <ActionCardView card={actionCard} />}
        {screen === "mandi" && <section className="surface panel"><p className="eyebrow">Decision support</p><h2>{t.mandi}</h2><p className="muted">Compare options before deciding. An officer or FPO confirms the next step.</p><div className="stack">{status.mandis.map((mandi) => <div className="check-row" key={mandi.mandi}><div><strong>{mandi.mandi}</strong><div className="muted small">{mandi.distance_km} km · {new Date(mandi.verified_at).toLocaleDateString()}</div></div><div style={{ textAlign: "right" }}><strong>₹{mandi.modal_price.toLocaleString("en-IN")}</strong><div className="small" style={{ color: mandi.change_pct < 0 ? "#b42318" : "#147a61" }}>{mandi.change_pct}% seasonal change</div></div></div>)}</div></section>}
        {screen === "copilot" && <section className="surface panel copilot-page"><div className="copilot-header"><span className="assistant-mark">✦</span><div><h2 style={{ marginBottom: 2 }}>{t.ask}</h2><span className="small muted">Simple explanations, approved next steps</span></div></div><div className="copilot-scroll">{messages.map((message) => <div className={`chat-bubble ${message.role}`} key={message.id}>{message.text}</div>)}</div><div className="quick-replies"><button className="quick-reply" onClick={() => replyTo("Why is my status red?")}>{t.why}</button><button className="quick-reply" onClick={() => replyTo("What should I do today?")}>{t.action}</button><button className="quick-reply" onClick={() => replyTo("Compare nearby markets")}>{t.mandi}</button></div><div className="chat-composer"><button className="icon-button" aria-label="Voice input" title="Voice input">⌁</button><input aria-label={t.askPlaceholder} value={copilotInput} onChange={(event) => setCopilotInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") replyTo(copilotInput); }} placeholder={t.askPlaceholder} /><Button onClick={() => replyTo(copilotInput)} disabled={!copilotInput.trim()}>{t.send}</Button></div></section>}
        {screen === "settings" && <section className="surface panel"><p className="eyebrow">Your choices</p><h2>{t.settings}</h2><p className="muted">{t.privacy}</p><ConsentToggle label="Save my support information" description="Needed to show your status again." value={consent.storage} onChange={updateConsent("storage")} /><ConsentToggle label="Allow officer contact" description="Lets an extension officer call or refer your case." value={consent.contact} onChange={updateConsent("contact")} /><ConsentToggle label="Include me in anonymous trends" description="Only group results are used." value={consent.analytics} onChange={updateConsent("analytics")} /><ConsentToggle label="Share a coarse repayment window" description="Timing only; no account or lender data." value={consent.due_window} onChange={updateConsent("due_window")} /><div className="row" style={{ marginTop: 16 }}><Button variant="secondary" onClick={() => { window.localStorage.removeItem("farmer-onboarded"); setOnboarded(false); }}>Review setup</Button><Button variant="ghost" onClick={() => setOnline(navigator.onLine)}>Refresh</Button></div></section>}
        {screen === "more" && <section className="surface panel stack"><div><p className="eyebrow">More</p><h2>{t.more}</h2></div><Button variant="secondary" onClick={() => setScreen("mandi")}>{t.mandi} <span className="spacer" />→</Button><Button variant="secondary" onClick={() => setScreen("settings")}>{t.settings} <span className="spacer" />→</Button></section>}
      </div>
      <nav className="bottom-nav" aria-label="Farmer navigation"><button className={`tab ${screen === "home" ? "active" : ""}`} onClick={() => setScreen("home")}><span className="nav-icon">⌂</span>Home</button><button className={`tab ${screen === "why" || screen === "action" ? "active" : ""}`} onClick={() => setScreen("why")}><span className="nav-icon">◌</span>{t.why}</button><button className={`tab ${screen === "copilot" ? "active" : ""}`} onClick={() => setScreen("copilot")}><span className="nav-icon">✦</span>{t.ask}</button><button className={`tab ${screen === "more" || screen === "mandi" || screen === "settings" ? "active" : ""}`} onClick={() => setScreen("more")}><span className="nav-icon">⋯</span>{t.more}</button></nav>
    </div></main>
  );
}
