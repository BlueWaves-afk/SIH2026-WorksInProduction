import { useEffect, useState } from "react";
import {
  Button,
  ConsentToggle,
  IconPicker,
  SeasonWheel,
  type ConsentState,
  type CopilotMessage,
} from "ui-kit";
import "ui-kit/styles.css";
import { loadFarmerStatus, submitFarmerProfile, type FarmerStatus } from "../api/client";
import { demoActionCard, demoMandis, demoRiskEvent } from "../demo";
import { ShieldDock, ShieldHome } from "./ShieldHome";
import { ShieldActionScreen, ShieldCopilotScreen, ShieldMarketScreen, ShieldMoreScreen, ShieldPrivacyScreen, ShieldStatusScreen } from "./ShieldScreens";

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
  const [locale, setLocale] = useState<Locale>("en");
  const [screen, setScreen] = useState<Screen>("home");
  const [onboarded, setOnboarded] = useState(() => window.localStorage.getItem("farmer-onboarded") === "true");
  const [crop, setCrop] = useState("cotton");
  const [season, setSeason] = useState<"kharif" | "rabi" | "zaid">("kharif");
  const [irrigationType, setIrrigationType] = useState("rainfed");
  const [consent, setConsent] = useState<ConsentState>(initialConsent);
  const [status, setStatus] = useState<FarmerStatus>({ risk_event: demoRiskEvent, action_card: demoActionCard, mandis: demoMandis, cached_at: new Date().toISOString(), source: "demo-fixture" });
  const [online, setOnline] = useState(() => navigator.onLine);
  const [submitting, setSubmitting] = useState(false);
  const [messages, setMessages] = useState<CopilotMessage[]>(() => starterMessages("en"));
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
  useEffect(() => { window.scrollTo({ top: 0, behavior: "auto" }); }, [screen]);

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
      <main className="app-shell farmer-shell shield-farmer-shell"><div className="app-container">
        <div className="shield-onboarding">
        <header className="shield-onboarding-intro"><div className="shield-wordmark"><span className="shield-logo" aria-hidden="true">KS</span><span><strong>KISANSETU</strong><small>Farmer support network</small></span></div><p className="shield-setup-kicker">PRIVATE · WORKS OFFLINE</p><h1>Support that reaches you <em>before the situation gets harder.</em></h1><p>A few simple choices help us explain local crop, weather and market signals.</p><div className="shield-setup-orb" aria-hidden="true"><span>☁</span><span>₹</span><span>🌱</span></div></header>
        <div className="surface panel stack shield-onboarding-card">
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
          <div className="shield-safety-note"><span className="shield-plan-check">✓</span><span><strong>Support only</strong><small>Your status is never a credit, loan-default or insurance score.</small></span></div>
          <Button onClick={() => void completeOnboarding()} disabled={!consent.storage || submitting}>{submitting ? "Saving…" : "Continue"}</Button>
        </div>
        </div>
      </div></main>
    );
  }

  return (
    <main className="app-shell farmer-shell shield-farmer-shell"><div className="app-container">
      {screen === "home" && <ShieldHome event={status.risk_event} updatedLabel={online ? t.updated : t.offline} onOpenWhy={() => setScreen("why")} onOpenAction={() => setScreen("action")} onOpenCopilot={() => setScreen("copilot")} onOpenMandi={() => setScreen("mandi")} />}
      {screen === "why" && <ShieldStatusScreen event={status.risk_event} onBack={() => setScreen("home")} onOpenAction={() => setScreen("action")} />}
      {screen === "action" && <ShieldActionScreen card={actionCard} onBack={() => setScreen("why")} onAsk={() => setScreen("copilot")} />}
      {screen === "mandi" && <ShieldMarketScreen mandis={status.mandis} onBack={() => setScreen("home")} />}
      {screen === "copilot" && <ShieldCopilotScreen messages={messages} input={copilotInput} placeholder={t.askPlaceholder} sendLabel={t.send} onInput={setCopilotInput} onReply={replyTo} onBack={() => setScreen("home")} />}
      {screen === "settings" && <ShieldPrivacyScreen consent={consent} privacyText={t.privacy} onUpdate={(key, value) => updateConsent(key)(value)} onReviewSetup={() => { window.localStorage.removeItem("farmer-onboarded"); setOnboarded(false); }} onBack={() => setScreen("more")} />}
      {screen === "more" && <ShieldMoreScreen locale={locale} localeName={t.name} onLocale={setLocale} onMarkets={() => setScreen("mandi")} onPrivacy={() => setScreen("settings")} onAsk={() => setScreen("copilot")} />}
      {(screen === "home" || screen === "more") && <ShieldDock screen={screen} labels={{ home: "Home", status: t.why, ask: t.ask, more: t.more }} onNavigate={setScreen} />}
    </div></main>
  );
}
