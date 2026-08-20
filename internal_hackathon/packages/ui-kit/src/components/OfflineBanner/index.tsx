export function OfflineBanner({ online, cachedAt }: { online: boolean; cachedAt?: string }) {
  if (online) return null;
  return <div className="notice warning" role="status">You are offline. Showing the last saved platform result{cachedAt ? ` from ${new Date(cachedAt).toLocaleString()}` : ""}. No new score is calculated on this device.</div>;
}
