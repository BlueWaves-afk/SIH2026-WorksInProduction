import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  Bean,
  Check,
  CircleDot,
  CloudRain,
  CloudSun,
  Droplets,
  Leaf,
  LockKeyhole,
  PencilLine,
  Sailboat,
  Sparkles,
  Sprout,
  Sun,
  Volume2,
  type LucideIcon,
} from "lucide-react";
import { ConsentToggle, type ConsentState } from "ui-kit";
import { useT } from "../i18n";

export type Locale = "en" | "hi" | "mr";
type Season = "kharif" | "rabi" | "zaid";

export interface OnboardingResult {
  crop: string;
  season: Season;
  irrigation: string;
  schemes: string[];
  consent: ConsentState;
  connected: boolean;
}

const LANGUAGES: Array<{ value: Locale; label: string; native: string; glyph: string }> = [
  { value: "mr", label: "Marathi", native: "मराठी", glyph: "अ" },
  { value: "hi", label: "Hindi", native: "हिंदी", glyph: "आ" },
  { value: "en", label: "English", native: "English", glyph: "A" },
];

const CROPS = [
  { value: "cotton", labelKey: "crop.cotton", icon: Sprout },
  { value: "soybean", labelKey: "crop.soybean", icon: Leaf },
  { value: "groundnut", labelKey: "crop.groundnut", icon: Bean },
  { value: "onion", labelKey: "crop.onion", icon: CircleDot },
];

const SEASONS: Array<{ value: Season; labelKey: string; icon: LucideIcon; hint: string }> = [
  { value: "kharif", labelKey: "season.kharif", icon: CloudRain, hint: "Jun – Oct" },
  { value: "rabi", labelKey: "season.rabi", icon: CloudSun, hint: "Nov – Mar" },
  { value: "zaid", labelKey: "season.zaid", icon: Sun, hint: "Mar – Jun" },
];

const IRRIGATION = [
  { value: "rainfed", labelKey: "irrigation.rainfed", icon: CloudRain },
  { value: "partial", labelKey: "irrigation.partial", icon: Droplets },
  { value: "assured", labelKey: "irrigation.assured", icon: Sailboat },
];

const SCHEMES = [
  { value: "pm-kisan", labelKey: "PM-Kisan" },
  { value: "pmfby", labelKey: "PMFBY" },
  { value: "kcc", labelKey: "KCC" },
  { value: "none", labelKey: "scheme.none" },
];

const STEP_TITLES = ["Language", "Connect", "Your farm", "Support", "Privacy"];

function OptionGrid({ label, hint, options, value, onChange, columns = 3, t }: {
  label: string; hint?: string;
  options: Array<{ value: string; labelKey: string; icon?: LucideIcon; hint?: string }>;
  value: string; onChange: (value: string) => void; columns?: number; t: (k: string) => string;
}) {
  return (
    <div className="shield-ob-field">
      <span className="shield-ob-label">{label}{hint && <small>{hint}</small>}</span>
      <div className="shield-ob-grid" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0,1fr))` }}>
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`shield-ob-option ${value === option.value ? "is-selected" : ""}`}
            aria-pressed={value === option.value}
            onClick={() => onChange(option.value)}
          >
            {option.icon && (() => {
              const Icon = option.icon;
              return <span className="shield-ob-icon" aria-hidden="true"><Icon size={25} strokeWidth={1.9} /></span>;
            })()}
            <strong>{t(option.labelKey)}</strong>
            {option.hint && <small>{option.hint}</small>}
          </button>
        ))}
      </div>
    </div>
  );
}

export function ShieldOnboarding({ locale, onLocale, onComplete, submitting, error }: {
  locale: Locale;
  onLocale: (locale: Locale) => void;
  onComplete: (result: OnboardingResult) => void;
  submitting: boolean;
  error?: string | null;
}) {
  const t = useT();
  const [step, setStep] = useState(0);
  const [crop, setCrop] = useState("cotton");
  const [season, setSeason] = useState<Season>("kharif");
  const [irrigation, setIrrigation] = useState("rainfed");
  const [schemes, setSchemes] = useState<string[]>([]);
  const [connectState, setConnectState] = useState<"idle" | "linking" | "linked" | "manual">("idle");
  const [consent, setConsent] = useState<ConsentState>({ storage: false, contact: false, analytics: false, due_window: false });

  const connected = connectState === "linked";

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [step]);

  function updateConsent(key: keyof ConsentState) {
    return (value: boolean) =>
      setConsent((current) => ({
        ...current,
        [key]: value,
        ...(key === "storage" && !value ? { contact: false, analytics: false, due_window: false } : {}),
      }));
  }

  function toggleScheme(value: string) {
    setSchemes((current) => {
      if (value === "none") return current.includes("none") ? [] : ["none"];
      const next = current.filter((item) => item !== "none");
      return next.includes(value) ? next.filter((item) => item !== value) : [...next, value];
    });
  }

  /** Mock AgriStack handshake. The real adapter (M3) performs a consented API Setu
   *  pull; either way we receive a token plus coarse profile fields — never Aadhaar. */
  function linkFarmerId() {
    setConnectState("linking");
    window.setTimeout(() => {
      setCrop("cotton");
      setIrrigation("rainfed");
      setSchemes(["pm-kisan"]);
      setConnectState("linked");
    }, 1400);
  }

  const canAdvance =
    step === 1 ? connectState === "linked" || connectState === "manual"
    : step === 4 ? consent.storage
    : true;

  function next() {
    if (step < 4) { setStep(step + 1); return; }
    onComplete({ crop, season, irrigation, schemes, consent, connected });
  }

  return (
    <div className="shield-onboarding">
      <header className="shield-ob-head">
        <div className="shield-wordmark">
          <span className="shield-logo" aria-hidden="true" />
          <span><strong>KISANSETU</strong><small>Support Nationwide</small></span>
        </div>
        <span className="shield-ob-count">{t("onboarding.step", { current: step + 1, total: 5 })}</span>
      </header>

      <div className="shield-ob-progress" role="progressbar" aria-valuenow={step + 1} aria-valuemin={1} aria-valuemax={5} aria-label={`Step ${step + 1} of 5: ${STEP_TITLES[step]}`}>
        {STEP_TITLES.map((title, index) => (
          <span key={title} className={index <= step ? "is-done" : ""} />
        ))}
      </div>

      <div className="shield-ob-body" key={step}>
        {step === 0 && (
          <>
            <section className="shield-ob-intro">
              <p className="shield-ob-kicker">{t("onboarding.kicker")}</p>
              <h1>{t("onboarding.lang.title")} <em>{t("onboarding.lang.accent")}</em></h1>
              <p className="shield-ob-sub">{t("onboarding.lang.sub")}</p>
            </section>
            <div className="shield-ob-langs">
              {LANGUAGES.map((language) => (
                <button
                  key={language.value}
                  type="button"
                  className={`shield-ob-lang ${locale === language.value ? "is-selected" : ""}`}
                  aria-pressed={locale === language.value}
                  onClick={() => onLocale(language.value)}
                >
                  <span className="shield-ob-glyph" aria-hidden="true">{language.glyph}</span>
                  <span className="shield-ob-lang-copy">
                    <strong>{language.native}</strong>
                    <small>{language.label}</small>
                  </span>
                  <i aria-hidden="true"><Volume2 size={15} strokeWidth={2.1} /></i>
                </button>
              ))}
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <section className="shield-ob-intro">
              <h1>{t("onboarding.connect.title")}</h1>
              <p className="shield-ob-sub">{t("onboarding.connect.sub")}</p>
            </section>

            {connectState !== "linked" ? (
              <div className="shield-ob-connect">
                <button type="button" className="shield-ob-connect-card is-primary" onClick={linkFarmerId} disabled={connectState === "linking"}>
                  <span className="shield-ob-connect-icon"><BadgeCheck size={22} strokeWidth={2} /></span>
                  <span>
                    <strong>{t("onboarding.connect.useId")}</strong>
                    <small>{t("onboarding.connect.useIdSub")}</small>
                  </span>
                  {connectState === "linking" ? <span className="shield-ob-linking" aria-label="Linking" /> : <ArrowRight size={18} strokeWidth={2.2} />}
                </button>
                <button type="button" className="shield-ob-connect-card" onClick={() => setConnectState("manual")}>
                  <span className="shield-ob-connect-icon is-plain"><PencilLine size={20} strokeWidth={2} /></span>
                  <span>
                    <strong>{t("onboarding.connect.manual")}</strong>
                    <small>{t("onboarding.connect.manualSub")}</small>
                  </span>
                  <ArrowRight size={18} strokeWidth={2.2} />
                </button>
              </div>
            ) : (
              <div className="shield-ob-linked">
                <span className="shield-ob-linked-mark"><Check size={22} strokeWidth={2.6} /></span>
                <strong>{t("onboarding.connect.linked")}</strong>
                <small>Nashik / Dindori · Cotton · Rain-fed · under 1 ha</small>
                <button type="button" onClick={() => { setConnectState("manual"); setSchemes([]); }}>{t("onboarding.connect.linkedAgain")}</button>
              </div>
            )}

            <div className="shield-ob-privacy-note">
              <LockKeyhole size={17} strokeWidth={2} />
              <span>{t("onboarding.connect.privacy")}</span>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <section className="shield-ob-intro">
              <h1>{t("onboarding.farm.title")}</h1>
              <p className="shield-ob-sub">{connected ? t("onboarding.farm.subLinked") : t("onboarding.farm.subManual")}</p>
            </section>
            <OptionGrid t={t} label={t("onboarding.farm.crop")} options={CROPS} value={crop} onChange={setCrop} columns={4} />
            <OptionGrid t={t} label={t("onboarding.farm.season")} options={SEASONS} value={season} onChange={(value) => setSeason(value as Season)} />
            <OptionGrid t={t} label={t("onboarding.farm.irrigation")} options={IRRIGATION} value={irrigation} onChange={setIrrigation} />
          </>
        )}

        {step === 3 && (
          <>
            <section className="shield-ob-intro">
              <h1>{t("onboarding.support.title")}</h1>
              <p className="shield-ob-sub">{t("onboarding.support.sub")}</p>
            </section>
            <div className="shield-ob-field">
              <span className="shield-ob-label">{t("onboarding.support.schemes")}{connected && <small>{t("onboarding.support.fromId")}</small>}</span>
              <div className="shield-ob-chips">
                {SCHEMES.map((scheme) => (
                  <button
                    key={scheme.value}
                    type="button"
                    className={`shield-ob-chip ${schemes.includes(scheme.value) ? "is-selected" : ""}`}
                    aria-pressed={schemes.includes(scheme.value)}
                    onClick={() => toggleScheme(scheme.value)}
                  >
                    {schemes.includes(scheme.value) && <Check size={14} strokeWidth={3} />}
                    {t(scheme.labelKey)}
                  </button>
                ))}
              </div>
            </div>
            <div className="shield-ob-optin">
              <ConsentToggle
                label={t("onboarding.support.dueTitle")}
                description={t("onboarding.support.dueBody")}
                value={consent.due_window}
                onChange={updateConsent("due_window")}
              />
            </div>
            <div className="shield-ob-privacy-note">
              <Sparkles size={17} strokeWidth={2} />
              <span>{t("onboarding.support.note")}</span>
            </div>
          </>
        )}

        {step === 4 && (
          <>
            <section className="shield-ob-intro">
              <h1>{t("onboarding.privacy.title")}</h1>
              <p className="shield-ob-sub">{t("onboarding.privacy.sub")}</p>
            </section>
            <div className="shield-ob-consents">
              <ConsentToggle label={t("onboarding.privacy.storage")} description={t("onboarding.privacy.storageBody")} value={consent.storage} onChange={updateConsent("storage")} />
              <ConsentToggle label={t("onboarding.privacy.contact")} description={t("onboarding.privacy.contactBody")} value={consent.contact} onChange={updateConsent("contact")} />
              <ConsentToggle label={t("onboarding.privacy.analytics")} description={t("onboarding.privacy.analyticsBody")} value={consent.analytics} onChange={updateConsent("analytics")} />
            </div>
            {!consent.storage && <p className="shield-ob-required">{t("onboarding.privacy.required")}</p>}
          </>
        )}
      </div>

      {error && <p className="auth-error shield-ob-submit-error" role="alert">{error}</p>}
      <footer className="shield-ob-foot">
        {step > 0 && (
          <button type="button" className="shield-ob-back" onClick={() => setStep(step - 1)} aria-label="Go back">
            <ArrowLeft size={19} strokeWidth={2.2} />
          </button>
        )}
        <button type="button" className="shield-ob-next" onClick={next} disabled={!canAdvance || submitting}>
          {submitting ? t("onboarding.saving") : step === 4 ? t("onboarding.finish") : t("onboarding.continue")}
          {!submitting && <ArrowRight size={18} strokeWidth={2.3} />}
        </button>
      </footer>
    </div>
  );
}
