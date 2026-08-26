import { createClient, type Session, type SupabaseClient } from "@supabase/supabase-js";

/** Supabase Auth expects the project root, not the REST endpoint path. */
export function normalizeSupabaseUrl(value: string | undefined): string | undefined {
  const trimmed = value?.trim().replace(/\/+$/, "");
  if (!trimmed) return undefined;
  return trimmed.replace(/\/(?:rest\/v1|auth\/v1)$/i, "");
}

const url = normalizeSupabaseUrl(import.meta.env.VITE_SUPABASE_URL as string | undefined);
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

export function friendlyAuthError(reason: unknown): string {
  const message = reason instanceof Error ? reason.message : String(reason ?? "");
  const normalized = message.toLowerCase();
  if (normalized.includes("failed to fetch") || normalized.includes("networkerror") || normalized.includes("fetch error")) {
    return "We could not reach Supabase Auth. Check that VITE_SUPABASE_URL is the project root (not /rest/v1) and that the public anon key is correct.";
  }
  if (normalized.includes("invalid login credentials")) {
    return "Email or password is incorrect. Confirm the email first if this account was just created.";
  }
  if (normalized.includes("email not confirmed")) {
    return "Confirm your work email from the message we sent, then sign in again.";
  }
  if (normalized.includes("rate limit") || normalized.includes("too many")) {
    return "Too many attempts. Wait a minute and try again.";
  }
  return message || "Officer sign-in failed. Please try again.";
}

/**
 * Browser-safe Supabase Auth boundary. Service keys never belong here.
 *
 * Farmer and officer workspaces are mounted together in the unified portal.
 * Reuse the browser singleton rather than constructing a second GoTrue client
 * against the same auth storage key.
 */
type SupabaseGlobal = typeof globalThis & { __kisanSetuSupabase?: SupabaseClient };
const browserGlobal = globalThis as SupabaseGlobal;

export const supabase = url && anonKey
  ? (browserGlobal.__kisanSetuSupabase ??= createClient(url, anonKey, { auth: { persistSession: true, autoRefreshToken: true } }))
  : null;
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

export async function signIn(email: string, password: string) {
  if (!supabase) throw new Error("Supabase Auth is not configured");
  const result = await supabase.auth.signInWithPassword({ email: email.trim().toLowerCase(), password });
  if (result.error) throw result.error;
  return result.data.session;
}

export async function signOut() {
  if (supabase) await supabase.auth.signOut();
  window.localStorage.removeItem("kisansetu.access_token");
}
