/**
 * Last-known-good farmer status.
 *
 * The service worker keeps the app shell and API responses available offline, but
 * the UI still needs to answer "what did we last actually know?" — and to say so
 * truthfully. Nothing here is a credential; it is the same advisory the farmer
 * already saw, kept so the status card is not blank without a network.
 */
const KEY = "farmer-status-v1";

export interface CachedStatus<T> {
  payload: T;
  cached_at: string;
}

export function readCachedStatus<T>(): CachedStatus<T> | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CachedStatus<T>;
    return parsed && parsed.payload ? parsed : null;
  } catch {
    return null; // corrupt or unavailable storage must never break the app
  }
}

export function writeCachedStatus<T>(payload: T): CachedStatus<T> {
  const entry: CachedStatus<T> = { payload, cached_at: new Date().toISOString() };
  try {
    window.localStorage.setItem(KEY, JSON.stringify(entry));
  } catch {
    /* private mode / quota: caching is best-effort, never required */
  }
  return entry;
}

export function clearCachedStatus() {
  try { window.localStorage.removeItem(KEY); } catch { /* no-op */ }
}

/** Human-friendly age for the offline banner, e.g. "2 hours ago". */
export function describeAge(iso: string, now = new Date()): string {
  const minutes = Math.max(0, Math.round((now.getTime() - new Date(iso).getTime()) / 60000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}
