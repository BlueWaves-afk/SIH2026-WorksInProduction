import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { ArrowRight, LockKeyhole, Mail, ShieldCheck } from "lucide-react";
import { authRequired, currentSession, observeSession, signIn, signOut, supabase } from "./supabase";

const OFFICER_ROLES = new Set(["extension_officer", "district_admin", "admin", "auditor"]);

export function OfficerAuthGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(authRequired);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
  if (loading) return <AuthFrame><p className="auth-kicker">OFFICER WORKSPACE</p><h1>Checking your secure session…</h1></AuthFrame>;
  if (!supabase) return <AuthFrame><p className="auth-kicker">SETUP REQUIRED</p><h1>Officer sign-in is not configured.</h1><p>Add the public Supabase URL and anonymous key to the Vercel environment.</p></AuthFrame>;

  const role = String(session?.user.app_metadata?.role ?? "");
  if (session && !OFFICER_ROLES.has(role)) {
    return <AuthFrame><div className="auth-mark"><ShieldCheck size={27} /></div><p className="auth-kicker">ACCESS RESTRICTED</p><h1>This account has no officer role.</h1><p>An administrator must assign an extension-officer or district role in Supabase app metadata.</p><button className="auth-submit" onClick={() => void signOut()}>Sign out</button></AuthFrame>;
  }
  if (session) return children;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const signedIn = await signIn(email.trim(), password);
      const signedInRole = String(signedIn?.user.app_metadata?.role ?? "");
      if (!OFFICER_ROLES.has(signedInRole)) {
        await signOut();
        setError("This account has not been assigned an officer role.");
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign-in failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthFrame>
      <div className="auth-mark"><ShieldCheck size={28} /></div>
      <p className="auth-kicker">KISANSETU OPERATIONS</p>
      <h1>Officer sign in</h1>
      <p>Use your authorised district or extension account.</p>
      <form className="auth-form" onSubmit={submit}>
        <label><span>Work email</span><div className="auth-input"><Mail size={18} /><input required type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} /></div></label>
        <label><span>Password</span><div className="auth-input"><LockKeyhole size={18} /><input required type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} /></div></label>
        {error && <p className="auth-error" role="alert">{error}</p>}
        <button className="auth-submit" disabled={submitting}>{submitting ? "Signing in…" : "Open officer workspace"}<ArrowRight size={18} /></button>
      </form>
      <small className="auth-footnote">Role and district access are verified again by the backend on every sensitive request.</small>
    </AuthFrame>
  );
}

function AuthFrame({ children }: { children: ReactNode }) {
  return <main className="auth-page is-officer"><section className="auth-card">{children}</section></main>;
}
