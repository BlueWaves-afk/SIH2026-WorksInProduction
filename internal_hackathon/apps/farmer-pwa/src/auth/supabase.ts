import { createClient, type Session, type SupabaseClient } from "@supabase/supabase-js";

/**
 * Supabase browser clients need the project root, not a REST endpoint. Older
 * deployment handoffs sometimes copied `.../rest/v1/` into VITE_SUPABASE_URL;
 * leaving that suffix makes GoTrue call `/rest/v1/auth/v1` and looks like a
 * bad credential or failed-fetch error. Normalize both accepted forms here
 * and in the backend settings boundary.
 */
export function normalizeSupabaseUrl(value: string | undefined): string | undefined {
  const trimmed = value?.trim().replace(/\/+$/, "");
  if (!trimmed) return undefined;
  return trimmed.replace(/\/(?:rest\/v1|auth\/v1)$/i, "");
}

const url = normalizeSupabaseUrl(import.meta.env.VITE_SUPABASE_URL as string | undefined);
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

export type AuthAction = "signin" | "signup" | "otp" | "session";

/** Turn provider/network failures into an actionable message for a farmer. */
export function friendlyAuthError(reason: unknown, action: AuthAction = "signin"): string {
  const message = reason instanceof Error ? reason.message : String(reason ?? "");
  const normalized = message.toLowerCase();
  if (normalized.includes("failed to fetch") || normalized.includes("networkerror") || normalized.includes("fetch error")) {
    return "We could not reach Supabase Auth. Check that the project URL is the root address (https://your-project.supabase.co), not /rest/v1, and that the public anon key is correct.";
  }
  if (normalized.includes("invalid login credentials")) {
    return "Email or password is incorrect. If you just created the account, confirm the email first, then sign in again.";
  }
  if (normalized.includes("email not confirmed")) {
    return "Confirm your email from the message we sent, then sign in again. You can resend it from the sign-up screen.";
  }
  if (normalized.includes("user already registered") || normalized.includes("already exists")) {
    return "An account with this email already exists. Switch to sign in instead.";
  }
  if (normalized.includes("rate limit") || normalized.includes("too many")) {
    return "Too many attempts. Wait a minute and try again.";
  }
  if (normalized.includes("signup") && normalized.includes("disabled")) {
    return "Email sign-up is disabled for this Supabase project. Enable Email provider in Supabase Auth settings.";
  }
  if (action === "otp" && normalized.includes("phone")) {
    return "Phone OTP could not be sent. Check the number in international format and the Supabase SMS provider configuration.";
  }
  return message || (action === "signup" ? "Account creation failed. Please try again." : "Sign-in failed. Please try again.");
}

export class AuthFlowError extends Error {
  constructor(public readonly code: "account_exists" | "invalid_phone", message: string) {
    super(message);
    this.name = "AuthFlowError";
  }
}

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
  const currentOrigin = typeof window !== "undefined" ? window.location.origin : undefined;
  if (configured) {
    try {
      const parsed = new URL(configured);
      const isLocalConfigured = ["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname);
      const isLocalCurrent = currentOrigin ? ["localhost", "127.0.0.1", "[::1]"].includes(new URL(currentOrigin).hostname) : false;
      // A stale localhost value in Vercel/Render must never send a production
      // farmer to a machine that cannot receive the confirmation callback.
      if (isLocalConfigured && currentOrigin && !isLocalCurrent) return currentOrigin;
      if (parsed.protocol === "http:" || parsed.protocol === "https:") return configured.replace(/\/+$/, "");
    } catch {
      // Fall through to the origin that actually opened the app.
    }
  }
  if (currentOrigin) return currentOrigin;
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
  const normalizedPhone = phone.trim().replace(/[()\s-]/g, "");
  const e164 = /^\d{10}$/.test(normalizedPhone) ? `+91${normalizedPhone}` : normalizedPhone;
  if (!/^\+[1-9]\d{7,14}$/.test(e164)) {
    throw new AuthFlowError("invalid_phone", "Enter a valid mobile number with country code, for example +91 98765 43210.");
  }
  const result = await supabase.auth.signInWithOtp({ phone: e164 });
  if (result.error) throw result.error;
}

export async function verifyPhoneOtp(phone: string, token: string) {
  if (!supabase) throw new Error("Supabase Auth is not configured");
  const normalizedPhone = phone.trim().replace(/[()\s-]/g, "");
  const e164 = /^\d{10}$/.test(normalizedPhone) ? `+91${normalizedPhone}` : normalizedPhone;
  if (!/^\+[1-9]\d{7,14}$/.test(e164)) {
    throw new AuthFlowError("invalid_phone", "Enter a valid mobile number with country code, for example +91 98765 43210.");
  }
  const result = await supabase.auth.verifyOtp({ phone: e164, token, type: "sms" });
  if (result.error) throw result.error;
  return result.data.session;
}

/** Email is a demo-friendly fallback for farmers when an SMS provider is not configured. */
export async function signInWithEmail(email: string, password: string) {
  if (!supabase) throw new Error("Supabase Auth is not configured");
  const result = await supabase.auth.signInWithPassword({ email: email.trim().toLowerCase(), password });
  if (result.error) throw result.error;
  return result.data.session;
}

export async function signUpWithEmail(email: string, password: string) {
  if (!supabase) throw new Error("Supabase Auth is not configured");
  const result = await supabase.auth.signUp({
    email: email.trim().toLowerCase(),
    password,
    options: { data: { role: "farmer" }, emailRedirectTo: authRedirectUrl() },
  });
  if (result.error) throw result.error;
  // Supabase intentionally returns an obfuscated user for an existing
  // account in some confirmation configurations. An empty identities array
  // is the documented signal; route the person to sign-in rather than leaving
  // them in a misleading "check your email" state.
  if (result.data.user && Array.isArray(result.data.user.identities) && result.data.user.identities.length === 0) {
    throw new AuthFlowError("account_exists", "An account with this email already exists. Switch to sign in instead.");
  }
  return result.data;
}

export async function resendSignupConfirmation(email: string) {
  if (!supabase) throw new Error("Supabase Auth is not configured");
  const result = await supabase.auth.resend({
    type: "signup",
    email: email.trim().toLowerCase(),
    options: { emailRedirectTo: authRedirectUrl() },
  });
  if (result.error) throw result.error;
}

export async function signOut() {
  if (supabase) await supabase.auth.signOut();
  window.localStorage.removeItem("kisansetu.access_token");
}
