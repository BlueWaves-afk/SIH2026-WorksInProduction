import { useEffect, useRef, useState } from "react";
import { type ConsentState, type CopilotMessage } from "ui-kit";
import "ui-kit/styles.css";
import { loadFarmerStatus, sendCopilotMessage, submitFarmerProfile, synthesizeSpeech, transcribeSpeech, type FarmerStatus } from "../api/client";
import { demoMode } from "../auth/supabase";
import { describeAge } from "../features/offline/statusCache";
import { demoActionCard, demoAlerts, demoMandis, demoRiskEvent } from "../demo";
import { ShieldDock, ShieldHome } from "./ShieldHome";
import { ShieldOnboarding, type OnboardingResult } from "./ShieldOnboarding";
import { ShieldAlertsScreen } from "./ShieldAlerts";
import { LocaleProvider, translate, type Locale as I18nLocale } from "../i18n";
import { ShieldActionScreen, ShieldCopilotScreen, ShieldMarketScreen, ShieldMoreScreen, ShieldPrivacyScreen, ShieldStatusScreen, type VoiceState } from "./ShieldScreens";

type Screen = "home" | "alerts" | "why" | "action" | "copilot" | "mandi" | "settings" | "more";
type Locale = "en" | "hi" | "mr";

/* Navigation depth drives the slide direction: deeper = slide in from the right. */
const DOCKLESS_SCREENS = new Set<Screen>(["why", "copilot"]);
const SCREEN_DEPTH: Record<Screen, number> = { home: 0, more: 0, alerts: 1, mandi: 1, copilot: 1, settings: 1, why: 2, action: 3 };

const copy: Record<Locale, {
  name: string; welcome: string; home: string; why: string; action: string; ask: string; mandi: string; settings: string;
  statusRed: string; statusGreen: string; updated: string; offline: string; assistantTitle: string; assistantBody: string;
  askPlaceholder: string; send: string; more: string; privacy: string; navStatus: string; navAsk: string;
}> = {
  en: { name: "English", welcome: "Farmer support", home: "Your support status", why: "Why this status", action: "Next steps", ask: "Ask support", mandi: "Nearby markets", settings: "Privacy", statusRed: "An agriculture officer should review this today.", statusGreen: "No urgent follow-up is currently needed.", updated: "Updated just now", offline: "Last saved status", assistantTitle: "Ask about your status", assistantBody: "Get a simple explanation or find the next safe step.", askPlaceholder: "Ask a question…", send: "Send", more: "More", privacy: "Your choices are yours to change.", navStatus: "Status", navAsk: "Ask" },
  hi: { name: "हिंदी", welcome: "किसान सहायता", home: "आपकी सहायता स्थिति", why: "यह स्थिति क्यों है", action: "अगले कदम", ask: "सहायता से पूछें", mandi: "पास की मंडियां", settings: "गोपनीयता", statusRed: "कृषि अधिकारी को आज इस मामले की समीक्षा करनी चाहिए।", statusGreen: "अभी तत्काल सहायता की जरूरत नहीं है।", updated: "अभी अपडेट किया गया", offline: "अंतिम सुरक्षित स्थिति", assistantTitle: "अपनी स्थिति के बारे में पूछें", assistantBody: "सरल भाषा में कारण और अगला सुरक्षित कदम जानें।", askPlaceholder: "सवाल लिखें…", send: "भेजें", more: "और", privacy: "आप अपनी पसंद कभी भी बदल सकते हैं।", navStatus: "स्थिति", navAsk: "पूछें" },
  mr: { name: "मराठी", welcome: "शेतकरी मदत", home: "तुमची मदत स्थिती", why: "ही स्थिती का आहे", action: "पुढची पावले", ask: "मदतीला विचारा", mandi: "जवळचे बाजार", settings: "गोपनीयता", statusRed: "कृषी अधिकाऱ्याने आज या प्रकरणाची पाहणी करावी.", statusGreen: "सध्या तातडीच्या मदतीची गरज नाही.", updated: "आत्ताच अपडेट", offline: "शेवटची जतन केलेली स्थिती", assistantTitle: "तुमच्या स्थितीबद्दल विचारा", assistantBody: "सोप्या भाषेत कारण आणि पुढचे सुरक्षित पाऊल जाणून घ्या.", askPlaceholder: "प्रश्न विचारा…", send: "पाठवा", more: "अधिक", privacy: "तुम्ही तुमची निवड कधीही बदलू शकता.", navStatus: "स्थिती", navAsk: "विचारा" },
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
  const [consent, setConsent] = useState<ConsentState>(initialConsent);
  const [status, setStatus] = useState<FarmerStatus | null>(() => demoMode ? { risk_event: demoRiskEvent, action_card: demoActionCard, mandis: demoMandis, cached_at: new Date().toISOString(), source: "demo-fixture" } : null);
  const [dataError, setDataError] = useState<string | null>(null);
  const [onboardingError, setOnboardingError] = useState<string | null>(null);
  const [online, setOnline] = useState(() => navigator.onLine);
  const [submitting, setSubmitting] = useState(false);
  const [messages, setMessages] = useState<CopilotMessage[]>(() => starterMessages("en"));
  const [copilotInput, setCopilotInput] = useState("");
  const [direction, setDirection] = useState<"forward" | "back">("forward");
  const [thinking, setThinking] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [voiceStatus, setVoiceStatus] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const voiceMountedRef = useRef(true);
  const t = copy[locale];
  const tr = translate(locale as I18nLocale);

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    if (onboarded) void refreshStatus();
    return () => { window.removeEventListener("online", onOnline); window.removeEventListener("offline", onOffline); };
  }, [onboarded]);

  useEffect(() => setMessages(starterMessages(locale)), [locale]);
  useEffect(() => { window.scrollTo({ top: 0, behavior: "auto" }); }, [screen]);
  useEffect(() => {
    voiceMountedRef.current = true;
    return () => {
      voiceMountedRef.current = false;
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      streamRef.current?.getTracks().forEach((track) => track.stop());
      audioRef.current?.pause();
      if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
    };
  }, []);

  // Say exactly where the status came from — never imply "live" when it is not.
  const statusLabel = status
    ? status.source === "api" && online
      ? tr("home.updated")
      : `${tr("home.offline")} · ${describeAge(status.cached_at)}`
    : "";

  const actionCard = localizedActionCard(locale);
  const updateConsent = (key: keyof ConsentState) => (value: boolean) => setConsent((current) => ({ ...current, [key]: value, ...(key === "storage" && !value ? { contact: false, analytics: false, due_window: false } : {}) }));

  function navigate(next: Screen) {
    setDirection(SCREEN_DEPTH[next] < SCREEN_DEPTH[screen] ? "back" : "forward");
    setScreen(next);
  }

  async function completeOnboarding(result: OnboardingResult) {
    setConsent(result.consent);
    setSubmitting(true);
    setOnboardingError(null);
    try {
      const created = await submitFarmerProfile({
        locale,
        crop: result.crop,
        season: result.season,
        irrigation: result.irrigation,
        consent_flags: result.consent,
      });
      window.localStorage.setItem("kisansetu.farmer_token", created.farmer_token);
    } catch (reason) {
      if (!demoMode) {
        setOnboardingError(reason instanceof Error ? reason.message : "Your profile could not be saved.");
        setSubmitting(false);
        return;
      }
    }
    window.localStorage.setItem("farmer-onboarded", "true");
    setOnboarded(true);
    setSubmitting(false);
  }

  async function refreshStatus() {
    setDataError(null);
    try {
      setStatus(await loadFarmerStatus());
    } catch (reason) {
      setDataError(reason instanceof Error ? reason.message : "Your support status is unavailable.");
    }
  }

  async function replyTo(text: string) {
    const question = text.trim();
    if (!question) return;
    setMessages((current) => [...current, { id: `farmer-${Date.now()}`, role: "farmer", text: question, created_at: new Date().toISOString() }]);
    setCopilotInput("");
    setThinking(true);
    try {
      // First-ever demo sessions have no backend profile. Keep the local
      // fixture path for those sessions; onboarded/deployed users use the
      // authenticated Sarvam-backed endpoint.
      const farmerToken = window.localStorage.getItem("kisansetu.farmer_token");
      if (demoMode && !farmerToken) throw new Error("demo fixture conversation");
      const response = await sendCopilotMessage(question, locale, messages);
      setMessages((current) => [...current, { id: `assistant-${Date.now()}`, role: "assistant", text: response.reply, created_at: new Date().toISOString() }]);
    } catch {
      const lower = question.toLowerCase();
      const answer = lower.includes("why") || lower.includes("का") || lower.includes("का?")
        ? status ? status.risk_event.contributors.slice(0, 2).map((driver) => driver.explanation).join(". ") + "." : "Your latest status is not available yet."
        : lower.includes("market") || lower.includes("mandi") || lower.includes("बाजार")
          ? "I can compare nearby market prices. Open Nearby markets to review the latest available quotes before deciding."
          : "The safest next step is to share your crop condition with the agriculture officer. I can show the approved action plan or explain any driver.";
      setMessages((current) => [...current, { id: `assistant-${Date.now()}`, role: "assistant", text: answer, created_at: new Date().toISOString() }]);
    } finally {
      setThinking(false);
    }
  }

  function stopPlayback() {
    audioRef.current?.pause();
    audioRef.current = null;
    if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
    audioUrlRef.current = null;
    setVoiceState("idle");
    setVoiceStatus(null);
  }

  async function toggleVoiceCapture() {
    if (voiceState === "playing") {
      stopPlayback();
      return;
    }
    if (voiceState === "recording") {
      recorderRef.current?.stop();
      return;
    }
    if (voiceState !== "idle") return;
    setVoiceError(null);
    setVoiceStatus(null);
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setVoiceError("Voice recording is not supported on this device. You can still type your question.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const preferredType = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"]
        .find((type) => MediaRecorder.isTypeSupported(type));
      const recorder = preferredType ? new MediaRecorder(stream, { mimeType: preferredType }) : new MediaRecorder(stream);
      recordingChunksRef.current = [];
      recorder.ondataavailable = (event) => { if (event.data.size) recordingChunksRef.current.push(event.data); };
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        recorderRef.current = null;
        const blob = new Blob(recordingChunksRef.current, { type: recorder.mimeType || preferredType || "audio/webm" });
        recordingChunksRef.current = [];
        if (!voiceMountedRef.current) return;
        setVoiceState("transcribing");
        setVoiceStatus("Understanding your voice note…");
        void transcribeSpeech(blob, locale)
          .then((result) => {
            if (!voiceMountedRef.current) return;
            setCopilotInput(result.text);
            setVoiceState("idle");
            setVoiceStatus("Voice note ready — review it before sending.");
          })
          .catch((reason) => {
            if (!voiceMountedRef.current) return;
            setVoiceState("idle");
            setVoiceStatus(null);
            setVoiceError(reason instanceof Error ? reason.message : "Voice transcription is unavailable. You can still type your question.");
          });
      };
      recorder.start();
      recorderRef.current = recorder;
      setVoiceState("recording");
      setVoiceStatus("Listening… tap the microphone to stop.");
    } catch (reason) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      setVoiceState("idle");
      setVoiceError(reason instanceof DOMException && reason.name === "NotAllowedError"
        ? "Microphone access was blocked. Allow microphone access or type your question instead."
        : "We could not start the microphone. You can still type your question.");
    }
  }

  async function playLastAnswer() {
    if (voiceState === "playing") {
      stopPlayback();
      return;
    }
    if (voiceState !== "idle") return;
    const lastAssistant = [...messages].reverse().find((message) => message.role === "assistant");
    if (!lastAssistant) return;
    setVoiceError(null);
    setVoiceState("synthesizing");
    setVoiceStatus("Preparing the spoken answer…");
    try {
      const audioBlob = await synthesizeSpeech(lastAssistant.text, locale);
      const url = URL.createObjectURL(audioBlob);
      audioUrlRef.current = url;
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => stopPlayback();
      audio.onerror = () => {
        if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
        audioUrlRef.current = null;
        audioRef.current = null;
        setVoiceState("idle");
        setVoiceStatus(null);
        setVoiceError("The spoken answer could not be played. You can read the answer above.");
      };
      await audio.play();
      setVoiceState("playing");
      setVoiceStatus("Playing the spoken answer…");
    } catch (reason) {
      if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
      audioRef.current = null;
      setVoiceState("idle");
      setVoiceStatus(null);
      setVoiceError(reason instanceof Error ? reason.message : "Spoken answers are unavailable. You can read the answer above.");
    }
  }

  if (!onboarded) {
    return (
      <LocaleProvider locale={locale}>
        <main className="app-shell farmer-shell shield-farmer-shell"><div className="app-container">
          <ShieldOnboarding locale={locale} onLocale={setLocale} onComplete={(result) => void completeOnboarding(result)} submitting={submitting} error={onboardingError} />
        </div></main>
      </LocaleProvider>
    );
  }

  if (!status) {
    return <main className="auth-page farmer-status-loading"><section className={`auth-card farmer-loading-card${dataError ? " is-error" : ""}`}>
      <div className="farmer-loading-mark" role="img" aria-label="KisanSetu">
        <span className="farmer-loading-logo is-base" aria-hidden="true" />
        <span className="farmer-loading-logo is-trace" aria-hidden="true" />
      </div>
      <p className="auth-kicker">FARMER SUPPORT</p>
      <h1>{dataError ? "We could not load your status." : "Loading your latest status…"}</h1>
      {dataError && <><p>{dataError}</p><button className="auth-submit" onClick={() => void refreshStatus()}>Try again</button></>}
    </section></main>;
  }

  return (
    <LocaleProvider locale={locale}>
    <main className="app-shell farmer-shell shield-farmer-shell"><div className="app-container">
      <div key={screen} className={`shield-view is-${direction}`}>
      {screen === "home" && <ShieldHome event={status.risk_event} updatedLabel={statusLabel} onOpenWhy={() => navigate("why")} onOpenAction={() => navigate("action")} onOpenCopilot={() => navigate("copilot")} onOpenMandi={() => navigate("mandi")} />}
      {screen === "alerts" && <ShieldAlertsScreen alerts={demoAlerts} onOpenAlert={() => navigate("why")} />}
      {screen === "why" && <ShieldStatusScreen event={status.risk_event} onBack={() => navigate("alerts")} onAsk={() => navigate("copilot")} />}
      {screen === "action" && <ShieldActionScreen card={actionCard} onBack={() => navigate("why")} onAsk={() => navigate("copilot")} />}
      {screen === "mandi" && <ShieldMarketScreen mandis={status.mandis} onBack={() => navigate("home")} />}
      {screen === "copilot" && <ShieldCopilotScreen messages={messages} thinking={thinking} input={copilotInput} placeholder={tr("copilot.placeholder")} sendLabel={t.send} onInput={setCopilotInput} onReply={replyTo} onBack={() => navigate("home")} voiceState={voiceState} voiceError={voiceError} voiceStatus={voiceStatus} onToggleRecording={() => void toggleVoiceCapture()} onPlayAnswer={() => void playLastAnswer()} />}
      {screen === "settings" && <ShieldPrivacyScreen consent={consent} privacyText={t.privacy} onUpdate={(key, value) => updateConsent(key)(value)} onReviewSetup={() => { window.localStorage.removeItem("farmer-onboarded"); setOnboarded(false); }} onBack={() => navigate("more")} />}
      {screen === "more" && <ShieldMoreScreen locale={locale} localeName={t.name} onLocale={setLocale} onMarkets={() => navigate("mandi")} onPrivacy={() => navigate("settings")} onAsk={() => navigate("copilot")} />}
      </div>
      {/* Detail screens carry their own bottom bar, so the dock steps aside. */}
      {!DOCKLESS_SCREENS.has(screen) && <ShieldDock screen={screen} labels={{ home: tr("nav.home"), status: tr("nav.status"), ask: tr("nav.ask"), more: tr("nav.more") }} onNavigate={navigate} />}
    </div></main>
    </LocaleProvider>
  );
}
