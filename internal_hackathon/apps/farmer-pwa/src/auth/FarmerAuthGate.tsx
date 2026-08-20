import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { ArrowRight, Leaf, LockKeyhole, Phone, ShieldCheck } from "lucide-react";
import { authRequired, currentSession, observeSession, sendPhoneOtp, supabase, verifyPhoneOtp } from "./supabase";

export function FarmerAuthGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(authRequired);
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
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
    try {
      if (stage === "phone") {
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
      <h1>{stage === "phone" ? "Open your KisanSetu support" : "Enter the 6-digit code"}</h1>
      <p>{stage === "phone" ? "Use the mobile number registered for your support profile." : `We sent a one-time code to ${phone}.`}</p>
      <form className="auth-form" onSubmit={submit}>
        {stage === "phone" ? (
          <label><span>Mobile number</span><div className="auth-input"><Phone size={19} /><input required inputMode="tel" autoComplete="tel" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="+91 98765 43210" /></div></label>
        ) : (
          <label><span>One-time code</span><div className="auth-input"><LockKeyhole size={19} /><input required inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={otp} onChange={(event) => setOtp(event.target.value.replace(/\D/g, ""))} placeholder="000000" /></div></label>
        )}
        {error && <p className="auth-error" role="alert">{error}</p>}
        <button className="auth-submit" disabled={submitting}>{submitting ? "Please wait…" : stage === "phone" ? "Send secure code" : "Verify and continue"}<ArrowRight size={19} /></button>
        {stage === "otp" && <button type="button" className="auth-link" onClick={() => { setStage("phone"); setOtp(""); setError(null); }}>Use a different number</button>}
      </form>
      <small className="auth-footnote">Your mobile number authenticates your session. Your opaque farmer token is never used as a password.</small>
    </AuthFrame>
  );
}

function AuthFrame({ children }: { children: ReactNode }) {
  return <main className="auth-page"><section className="auth-card">{children}</section></main>;
}
