import { createClient, type Session } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

/** Browser-safe Supabase Auth boundary. Service keys never belong here. */
export const supabase = url && anonKey ? createClient(url, anonKey, { auth: { persistSession: true, autoRefreshToken: true } }) : null;
export const demoMode = import.meta.env.DEV || import.meta.env.VITE_DEMO_MODE === "true";
const configuredAuthFlag = import.meta.env.VITE_AUTH_REQUIRED as string | undefined;
export const authRequired = configuredAuthFlag ? configuredAuthFlag === "true" : !demoMode;

export async function accessToken(): Promise<string | null> {
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) return data.session.access_token;
  }
  return demoMode ? window.localStorage.getItem("kisansetu.access_token") : null;
}

export async function currentSession(): Promise<Session | null> {
  if (!supabase) return null;
  const { data, error } = await supabase.auth.getSession();
  if (error) throw error;
  return data.session;
}

export function observeSession(callback: (session: Session | null) => void): () => void {
  if (!supabase) return () => undefined;
  const { data } = supabase.auth.onAuthStateChange((_event, session) => callback(session));
  return () => data.subscription.unsubscribe();
}

export async function sendPhoneOtp(phone: string) {
  if (!supabase) throw new Error("Supabase Auth is not configured");
  const result = await supabase.auth.signInWithOtp({ phone });
  if (result.error) throw result.error;
}

export async function verifyPhoneOtp(phone: string, token: string) {
  if (!supabase) throw new Error("Supabase Auth is not configured");
  const result = await supabase.auth.verifyOtp({ phone, token, type: "sms" });
  if (result.error) throw result.error;
  return result.data.session;
}

export async function signOut() {
  if (supabase) await supabase.auth.signOut();
  window.localStorage.removeItem("kisansetu.access_token");
}
