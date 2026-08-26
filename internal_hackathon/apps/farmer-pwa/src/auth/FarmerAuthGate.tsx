import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { ArrowRight, BriefcaseBusiness, LockKeyhole, Mail, Phone } from "lucide-react";
import { App as OfficerDashboard } from "../../../officer-dashboard/src/app/App";
import { AuthFlowError, authRequired, currentSession, friendlyAuthError, observeSession, resendSignupConfirmation, sendPhoneOtp, signInWithEmail, signOut, signUpWithEmail, supabase, verifyPhoneOtp } from "./supabase";

const OFFICER_ROLES = new Set(["extension_officer", "district_admin", "admin", "auditor"]);

export function FarmerAuthGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(authRequired);
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [method, setMethod] = useState<"phone" | "email">("phone");
  const [emailMode, setEmailMode] = useState<"signin" | "signup">("signin");
  const [emailConfirmation, setEmailConfirmation] = useState(false);
  const [stage, setStage] = useState<"phone" | "otp">("phone");
  const [portal, setPortal] = useState<"farmer" | "officer">("farmer");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (!authRequired) return;
    let active = true;
    const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const authErrorCode = hashParams.get("error_code") || hashParams.get("error");
    if (authErrorCode) {
      const description = hashParams.get("error_description") || "The confirmation link is invalid or has expired.";
      setError(`${description} Request a new confirmation email.`);
      window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
    }
    void currentSession()
      .then((value) => { if (active) setSession(value); })
      .catch(() => { if (active) setError("Your saved session could not be restored."); })
      .finally(() => { if (active) setLoading(false); });
    const unsubscribe = observeSession((value) => { setSession(value); setLoading(false); });
    return () => { active = false; unsubscribe(); };
  }, []);

  if (!authRequired) return children;
  if (loading) return <AuthFrame><p className="auth-kicker">SECURE FARMER ACCESS</p><h1>Restoring your private session…</h1></AuthFrame>;
  if (session) {
    // Only app_metadata is trusted for elevation; user_metadata is editable by
    // the end user and must never grant officer access.
    const role = String(session.user.app_metadata?.role ?? "").toLowerCase();
    return OFFICER_ROLES.has(role) ? <OfficerDashboard /> : children;
  }
  if (!supabase) return <AuthFrame><p className="auth-kicker">SETUP REQUIRED</p><h1>Farmer sign-in is not configured.</h1><p>Add the public Supabase URL and anonymous key to the Vercel environment.</p></AuthFrame>;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (method === "email" && emailConfirmation) {
        await resendSignupConfirmation(email.trim());
        setEmailConfirmation(true);
        return;
      }
      setEmailConfirmation(false);
      if (method === "email") {
        if (emailMode === "signup") {
          const result = await signUpWithEmail(email.trim(), password);
          if (result.session) setSession(result.session);
          setEmailConfirmation(!result.session);
        } else {
          const signedIn = await signInWithEmail(email.trim(), password);
          if (signedIn) setSession(signedIn);
        }
      } else if (stage === "phone") {
        await sendPhoneOtp(phone.trim());
        setStage("otp");
      } else {
        const verified = await verifyPhoneOtp(phone.trim(), otp.trim());
        if (verified) setSession(verified);
      }
    } catch (reason) {
      if (reason instanceof AuthFlowError && reason.code === "account_exists") {
        setEmailMode("signin");
        setEmailConfirmation(false);
      }
      const action = method === "email" ? (emailMode === "signup" ? "signup" : "signin") : stage === "phone" ? "otp" : "signin";
      setError(friendlyAuthError(reason, action));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthFrame>
      <div className="auth-brand-logo" aria-label="KisanSetu" role="img" />
      <p className="auth-kicker">PRIVATE · CONSENT-BASED</p>
      <div className="auth-role-panels" role="tablist" aria-label="KisanSetu access type">
        <button type="button" role="tab" aria-selected={portal === "farmer"} className={`auth-role-panel ${portal === "farmer" ? "is-active" : ""}`} onClick={() => { setPortal("farmer"); setError(null); }}>
          <span className="auth-role-logo" aria-hidden="true" />
          <strong>Farmer access</strong>
          <small>Phone OTP or email</small>
        </button>
        <button type="button" role="tab" aria-selected={portal === "officer"} className={`auth-role-panel ${portal === "officer" ? "is-active" : ""}`} onClick={() => { setPortal("officer"); setError(null); }}>
          <span className="auth-role-icon" aria-hidden="true"><BriefcaseBusiness size={20} /></span>
          <strong>Officer access</strong>
          <small>Work email and password</small>
        </button>
      </div>
      <AnimatePresence mode="wait" initial={false}>
        {portal === "officer" ? <motion.div key="officer" {...(reduceMotion ? reducedPanelMotion : panelMotion)}><OfficerAccessPanel /></motion.div> : (
        <motion.div key="farmer" {...(reduceMotion ? reducedPanelMotion : panelMotion)}>
          <h1>{method === "email" ? (emailMode === "signup" ? "Create your farmer account" : "Open your KisanSetu support") : stage === "phone" ? "Open your KisanSetu support" : "Enter the 6-digit code"}</h1>
          <p>{emailConfirmation ? "Check your email to confirm your account, then return here to sign in." : method === "email" ? "Email works as a demo fallback while phone OTP is being connected." : stage === "phone" ? "Use the mobile number registered for your support profile." : `We sent a one-time code to ${phone}.`}</p>
          <div className="auth-methods" role="tablist" aria-label="Sign-in method">
            <button type="button" className={method === "phone" ? "is-active" : ""} onClick={() => { setMethod("phone"); setStage("phone"); setError(null); }}><Phone size={16} /> Phone OTP</button>
            <button type="button" className={method === "email" ? "is-active" : ""} onClick={() => { setMethod("email"); setError(null); }}><Mail size={16} /> Email</button>
          </div>
          <form className="auth-form" onSubmit={submit}>
            {method === "email" ? (
              <>
                <label><span>Email address</span><div className="auth-input"><Mail size={19} /><input required type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></div></label>
                <label><span>Password</span><div className="auth-input"><LockKeyhole size={19} /><input required type="password" minLength={8} autoComplete={emailMode === "signup" ? "new-password" : "current-password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" /></div></label>
              </>
            ) : stage === "phone" ? (
              <label><span>Mobile number</span><div className="auth-input"><Phone size={19} /><input required inputMode="tel" autoComplete="tel" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="+91 98765 43210" /></div></label>
            ) : (
              <label><span>One-time code</span><div className="auth-input"><LockKeyhole size={19} /><input required inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={otp} onChange={(event) => setOtp(event.target.value.replace(/\D/g, ""))} placeholder="000000" /></div></label>
            )}
            {error && <p className="auth-error" role="alert">{error}</p>}
            <button className="auth-submit" disabled={submitting}>{submitting ? "Please wait…" : method === "email" && emailConfirmation ? "Resend confirmation email" : method === "email" ? (emailMode === "signup" ? "Create account" : "Sign in with email") : stage === "phone" ? "Send secure code" : "Verify and continue"}<ArrowRight size={19} /></button>
            {method === "email" && <button type="button" className="auth-link" onClick={() => { setEmailMode(emailMode === "signin" ? "signup" : "signin"); setEmailConfirmation(false); setError(null); }}>{emailMode === "signin" ? "New here? Create an account" : "Already registered? Sign in"}</button>}
            {method === "phone" && stage === "otp" && <button type="button" className="auth-link" onClick={() => { setStage("phone"); setOtp(""); setError(null); }}>Use a different number</button>}
          </form>
          <small className="auth-footnote">Your mobile number authenticates your session. Your opaque farmer token is never used as a password.</small>
        </motion.div>
      )}
      </AnimatePresence>
    </AuthFrame>
  );
}

function OfficerAccessPanel() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitOfficer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const signedIn = await signInWithEmail(email.trim(), password);
      const role = String(signedIn?.user.app_metadata?.role ?? "");
      if (!OFFICER_ROLES.has(role)) {
        await signOut();
        throw new Error("This account has not been assigned an officer role.");
      }
      // The officer workspace is part of this same Vercel build. The role-aware
      // session branch above renders it without a second deployment or redirect.
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Officer sign-in failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <h1>Officer sign in</h1>
      <p>Use your authorised district or extension account. Farmer accounts cannot open this workspace.</p>
      <form className="auth-form" onSubmit={submitOfficer}>
        <label><span>Work email</span><div className="auth-input"><Mail size={19} /><input required type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="officer@department.gov.in" /></div></label>
        <label><span>Password</span><div className="auth-input"><LockKeyhole size={19} /><input required type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Your work password" /></div></label>
        {error && <p className="auth-error" role="alert">{error}</p>}
        <button className="auth-submit" disabled={submitting}>{submitting ? "Checking access…" : "Open officer workspace"}<ArrowRight size={19} /></button>
      </form>
      <small className="auth-footnote">Officer role and district access are verified by Supabase and the backend.</small>
    </>
  );
}

function AuthFrame({ children }: { children: ReactNode }) {
  const reduceMotion = useReducedMotion();
  return <main className="auth-page"><motion.section className="auth-card" initial={reduceMotion ? false : { opacity: 0, y: 18, scale: 0.985 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: reduceMotion ? 0 : 0.42, ease: [0.22, 0.9, 0.28, 1] }}>{children}</motion.section></main>;
}

const panelMotion = {
  initial: { opacity: 0, x: 14 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -10 },
  transition: { duration: 0.24, ease: "easeOut" as const },
};

const reducedPanelMotion = {
  initial: false,
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 1, x: 0 },
  transition: { duration: 0 },
};
