import {
  ArrowLeft,
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
  MapPin,
  MessageCircle,
  Mic,
  Search,
  SendHorizontal,
  ShieldCheck,
  Sprout,
  Store,
  UserRound,
} from "lucide-react";
import { ConsentToggle, type ActionCard, type ConsentState, type Contributor, type CopilotMessage, type MandiQuote, type RiskEvent } from "ui-kit";

function InnerHeader({ title, subtitle, onBack }: { title: string; subtitle?: string; onBack: () => void }) {
  return (
    <header className="shield-inner-header">
      <button onClick={onBack} aria-label="Go back"><ArrowLeft size={20} /></button>
      <span><strong>{title}</strong>{subtitle && <small>{subtitle}</small>}</span>
      <button className="shield-inner-mark" aria-label="KisanSetu"><ShieldCheck size={20} /></button>
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

function DriverUpdate({ driver, index }: { driver: Contributor; index: number }) {
  const Icon = DRIVER_ICONS[driver.signal] ?? BellRing;
  return (
    <article className="shield-timeline-item">
      <span className="shield-timeline-dot" />
      <span className="shield-timeline-date">{index === 0 ? "Latest signal" : new Date(driver.observed_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</span>
      <div className="shield-timeline-bubble">
        <span><Icon size={19} /></span>
        <span><strong>{driver.explanation}</strong><small>{driver.source}</small></span>
        <b>+{Math.round(driver.points)}</b>
      </div>
    </article>
  );
}

export function ShieldStatusScreen({ event, onBack, onOpenAction }: { event: RiskEvent; onBack: () => void; onOpenAction: () => void }) {
  return (
    <div className="shield-screen">
      <InnerHeader title="Field alert" subtitle="Dindori, Nashik" onBack={onBack} />
      <section className="shield-detail-hero">
        <div className="shield-detail-badges"><span>{event.score}/100 support score</span><span><i /> Live</span></div>
        <div><small>COTTON FIELD UPDATE</small><h1>Support is recommended today</h1><p>Three independent signals are reinforcing the same support need.</p></div>
      </section>
      <section className="shield-timeline-section">
        <div className="shield-section-heading"><div><span>EXPLAINED CLEARLY</span><h2>Why this alert?</h2></div><b>{Math.round(event.confidence * 100)}% confidence</b></div>
        <div className="shield-timeline">{event.contributors.slice(0, 4).map((driver, index) => <DriverUpdate key={`${driver.signal}-${driver.observed_at}`} driver={driver} index={index} />)}</div>
      </section>
      <div className="shield-safety-note"><LockKeyhole size={18} /><span><strong>Support signal only</strong><small>{event.disclaimer}</small></span></div>
      <button className="shield-primary-cta" onClick={onOpenAction}>See the recommended plan <ChevronRight size={18} /></button>
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
  return (
    <div className="shield-screen">
      <InnerHeader title="Nearby markets" subtitle="Compare before selling" onBack={onBack} />
      <label className="shield-search"><Search size={18} /><input aria-label="Search markets" placeholder="Search this area" /><button aria-label="Market filters">⌁</button></label>
      <section className="shield-market-map" aria-label="Nearby market map">
        <span className="shield-map-road road-one" /><span className="shield-map-road road-two" /><span className="shield-map-road road-three" />
        <span className="shield-map-pin pin-one"><Store size={15} /></span><span className="shield-map-pin pin-two"><IndianRupee size={15} /></span><span className="shield-map-pin pin-three"><Store size={15} /></span>
        <span className="shield-current-location"><i /><b>Dindori</b></span>
      </section>
      <section className="shield-market-list">
        <div className="shield-section-heading"><div><span>PRICE OPTIONS</span><h2>Markets near you</h2></div><b>Today</b></div>
        {mandis.map((mandi, index) => (
          <article key={mandi.mandi} className={`shield-market-row ${index === 1 ? "best" : ""}`}>
            <span className="shield-market-rank">{index === 1 ? <ShieldCheck size={18} /> : index + 1}</span>
            <span><strong>{mandi.mandi}</strong><small><MapPin size={12} /> {mandi.distance_km} km away · verified today</small></span>
            <span><strong>₹{mandi.modal_price.toLocaleString("en-IN")}</strong><small>{mandi.change_pct}% seasonal</small></span>
          </article>
        ))}
      </section>
      <div className="shield-safety-note"><IndianRupee size={18} /><span><strong>Compare, then confirm</strong><small>Your FPO or officer confirms availability and grade before you travel.</small></span></div>
    </div>
  );
}

export function ShieldCopilotScreen({ messages, input, placeholder, sendLabel, onInput, onReply, onBack }: { messages: CopilotMessage[]; input: string; placeholder: string; sendLabel: string; onInput: (value: string) => void; onReply: (value: string) => void; onBack: () => void }) {
  return (
    <div className="shield-screen shield-agent-screen">
      <InnerHeader title="Support copilot" subtitle="Grounded in your field signals" onBack={onBack} />
      <section className="shield-agent-status">
        <div className="shield-agent-orbit"><span><UserRound size={21} /></span><i /><span><Bot size={21} /></span></div>
        <small>CONNECTED TO YOUR STATUS</small><h1>Ask in simple language</h1><p>The copilot explains approved information. It cannot change your score or send anything without permission.</p>
      </section>
      <div className="shield-chat-log" aria-live="polite">
        {messages.map((message) => <div key={message.id} className={`shield-chat-message ${message.role}`}><span>{message.role === "assistant" ? <Bot size={17} /> : <UserRound size={17} />}</span><p>{message.text}</p></div>)}
      </div>
      <div className="shield-quick-prompts"><button onClick={() => onReply("Why is my status red?")}>Why this alert?</button><button onClick={() => onReply("What should I do today?")}>What should I do?</button><button onClick={() => onReply("Compare nearby markets")}>Compare markets</button></div>
      <div className="shield-chat-composer">
        <button aria-label="Voice input"><Mic size={19} /></button>
        <input value={input} onChange={(event) => onInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") onReply(input); }} placeholder={placeholder} aria-label={placeholder} />
        <button aria-label={sendLabel} disabled={!input.trim()} onClick={() => onReply(input)}><SendHorizontal size={18} /></button>
      </div>
    </div>
  );
}

export function ShieldPrivacyScreen({ consent, privacyText, onUpdate, onReviewSetup, onBack }: { consent: ConsentState; privacyText: string; onUpdate: (key: keyof ConsentState, value: boolean) => void; onReviewSetup: () => void; onBack: () => void }) {
  return (
    <div className="shield-screen">
      <InnerHeader title="Privacy & consent" subtitle="Your choices stay editable" onBack={onBack} />
      <section className="shield-privacy-hero"><span><LockKeyhole size={25} /></span><h1>Your information, your choice</h1><p>{privacyText}</p></section>
      <section className="shield-consent-card">
        <ConsentToggle label="Save my support information" description="Needed to show your status again." value={consent.storage} onChange={(value) => onUpdate("storage", value)} />
        <ConsentToggle label="Allow officer contact" description="Lets an extension officer call or refer your case." value={consent.contact} onChange={(value) => onUpdate("contact", value)} />
        <ConsentToggle label="Include me in anonymous trends" description="Only group results are used." value={consent.analytics} onChange={(value) => onUpdate("analytics", value)} />
        <ConsentToggle label="Share a coarse repayment window" description="Timing only; no account or lender data." value={consent.due_window} onChange={(value) => onUpdate("due_window", value)} />
      </section>
      <button className="shield-secondary-cta" onClick={onReviewSetup}>Review my setup <ChevronRight size={18} /></button>
    </div>
  );
}

export function ShieldMoreScreen({ locale, localeName, onLocale, onMarkets, onPrivacy, onAsk }: { locale: string; localeName: string; onLocale: (locale: "en" | "hi" | "mr") => void; onMarkets: () => void; onPrivacy: () => void; onAsk: () => void }) {
  return (
    <div className="shield-screen">
      <section className="shield-profile-hero">
        <span className="shield-profile-avatar"><UserRound size={35} /></span>
        <h1>Your support space</h1><p>Dindori · Cotton · Kharif</p>
        <div><span><b>74</b><small>Support score</small></span><i /><span><b>86%</b><small>Confidence</small></span></div>
      </section>
      <section className="shield-menu-card">
        <button onClick={onMarkets}><span><Store size={19} /></span><span><strong>Nearby markets</strong><small>Compare today’s options</small></span><ChevronRight size={18} /></button>
        <button onClick={onAsk}><span><Headphones size={19} /></span><span><strong>Support copilot</strong><small>Ask about your status</small></span><ChevronRight size={18} /></button>
        <button onClick={onPrivacy}><span><LockKeyhole size={19} /></span><span><strong>Privacy & consent</strong><small>Control how information is used</small></span><ChevronRight size={18} /></button>
      </section>
      <label className="shield-language-row"><span><Languages size={19} /></span><span><strong>App language</strong><small>{localeName}</small></span><select aria-label="App language" value={locale} onChange={(event) => onLocale(event.target.value as "en" | "hi" | "mr")}><option value="mr">मराठी</option><option value="hi">हिंदी</option><option value="en">English</option></select></label>
      <div className="shield-safety-note"><ShieldCheck size={18} /><span><strong>KisanSetu support network</strong><small>Your score is for support prioritisation, never for credit or insurance decisions.</small></span></div>
    </div>
  );
}
