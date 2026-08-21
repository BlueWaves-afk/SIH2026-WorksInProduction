import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { ArrowRight, Leaf, LockKeyhole, Mail, Phone, ShieldCheck } from "lucide-react";
import { authRequired, currentSession, observeSession, sendPhoneOtp, signInWithEmail, signUpWithEmail, supabase, verifyPhoneOtp } from "./supabase";

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
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authRequired) return;
    let active = true;
    void currentSession()
      .then((value) => { if (active) setSession(value); })
      .catch(() => { if (active) setError("Your saved session could not be restored."); })
      .finally(() => { if (active) setLoading(false); });
    const unsubscribe = observeSession((value) => { setSession(value); setLoading(false); });
    return () => { active = false; unsubscribe(); };
  }, []);

  if (!authRequired) return children;
  if (loading) return <AuthFrame><p className="auth-kicker">SECURE FARMER ACCESS</p><h1>Restoring your private session…</h1></AuthFrame>;
  if (session) return children;
  if (!supabase) return <AuthFrame><p className="auth-kicker">SETUP REQUIRED</p><h1>Farmer sign-in is not configured.</h1><p>Add the public Supabase URL and anonymous key to the Vercel environment.</p></AuthFrame>;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setEmailConfirmation(false);
    try {
      if (method === "email") {
        if (emailMode === "signup") {
          const result = await signUpWithEmail(email.trim(), password);
          setEmailConfirmation(!result.session);
        } else {
          await signInWithEmail(email.trim(), password);
        }
      } else if (stage === "phone") {
        await sendPhoneOtp(phone.trim());
        setStage("otp");
      } else {
        await verifyPhoneOtp(phone.trim(), otp.trim());
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign-in failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthFrame>
      <div className="auth-mark"><Leaf size={28} /><ShieldCheck size={18} /></div>
      <p className="auth-kicker">PRIVATE · CONSENT-BASED</p>
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
        <button className="auth-submit" disabled={submitting || emailConfirmation}>{submitting ? "Please wait…" : method === "email" ? (emailMode === "signup" ? "Create account" : "Sign in with email") : stage === "phone" ? "Send secure code" : "Verify and continue"}<ArrowRight size={19} /></button>
        {method === "email" && <button type="button" className="auth-link" onClick={() => { setEmailMode(emailMode === "signin" ? "signup" : "signin"); setEmailConfirmation(false); setError(null); }}>{emailMode === "signin" ? "New here? Create an account" : "Already registered? Sign in"}</button>}
        {method === "phone" && stage === "otp" && <button type="button" className="auth-link" onClick={() => { setStage("phone"); setOtp(""); setError(null); }}>Use a different number</button>}
      </form>
      <small className="auth-footnote">Your mobile number authenticates your session. Your opaque farmer token is never used as a password.</small>
    </AuthFrame>
  );
}

function AuthFrame({ children }: { children: ReactNode }) {
  return <main className="auth-page"><section className="auth-card">{children}</section></main>;
}
