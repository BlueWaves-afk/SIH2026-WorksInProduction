export function StaleBadge({ stale, label = "Last known result" }: { stale: boolean; label?: string }) {
  return stale ? <span className="band-chip amber" role="status">{label}</span> : null;
}
