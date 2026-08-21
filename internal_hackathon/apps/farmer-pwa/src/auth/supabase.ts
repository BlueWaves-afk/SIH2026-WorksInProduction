import { createClient, type Session, type SupabaseClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

/**
 * Browser-safe Supabase Auth boundary. Service keys never belong here.
 *
 * The unified portal imports the farmer and officer auth modules in the same
 * browser context. Keep one client per Supabase project so GoTrue does not
 * create competing listeners for the same `sb-*-auth-token` storage key.
 */
type SupabaseGlobal = typeof globalThis & { __kisanSetuSupabase?: SupabaseClient };
const browserGlobal = globalThis as SupabaseGlobal;

export const supabase = url && anonKey
  ? (browserGlobal.__kisanSetuSupabase ??= createClient(url, anonKey, { auth: { persistSession: true, autoRefreshToken: true } }))
  : null;
export const demoMode = import.meta.env.DEV || import.meta.env.VITE_DEMO_MODE === "true";
const configuredAuthFlag = import.meta.env.VITE_AUTH_REQUIRED as string | undefined;
export const authRequired = configuredAuthFlag ? configuredAuthFlag === "true" : !demoMode;

/**
 * Supabase uses the project Site URL when a signup call does not provide a
 * redirect. That default is often localhost in a new project, so production
 * confirmation links can send a farmer to the wrong host. Prefer an explicit
 * deployment URL, then fall back to the origin that actually opened the app.
 */
export function authRedirectUrl(): string {
  const configured = (import.meta.env.VITE_AUTH_REDIRECT_URL as string | undefined)?.trim();
  if (configured) return configured.replace(/\/+$/, "");
  if (typeof window !== "undefined") return window.location.origin;
  return "http://localhost:5173";
}

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

/** Email is a demo-friendly fallback for farmers when an SMS provider is not configured. */
export async function signInWithEmail(email: string, password: string) {
  if (!supabase) throw new Error("Supabase Auth is not configured");
  const result = await supabase.auth.signInWithPassword({ email, password });
  if (result.error) throw result.error;
  return result.data.session;
}

export async function signUpWithEmail(email: string, password: string) {
  if (!supabase) throw new Error("Supabase Auth is not configured");
  const result = await supabase.auth.signUp({
    email,
    password,
    options: { data: { role: "farmer" }, emailRedirectTo: authRedirectUrl() },
  });
  if (result.error) throw result.error;
  return result.data;
}

export async function resendSignupConfirmation(email: string) {
  if (!supabase) throw new Error("Supabase Auth is not configured");
  const result = await supabase.auth.resend({
    type: "signup",
    email,
    options: { emailRedirectTo: authRedirectUrl() },
  });
  if (result.error) throw result.error;
}

export async function signOut() {
  if (supabase) await supabase.auth.signOut();
  window.localStorage.removeItem("kisansetu.access_token");
}
