import type { Contributor } from "../../types";

const ICONS: Record<string, string> = {
  rainfall_deficit: "☁️",
  rainfall_excess: "🌧️",
  satellite_crop_stress: "🌿",
  pest_pressure: "🐛",
  repayment_window: "📅",
  price_shock: "📉",
  farmer_report: "🗣️",
};

export function DriverPictogramCard({ contributor }: { contributor: Contributor }) {
  const percentage = contributor.max_points ? Math.round((contributor.points / contributor.max_points) * 100) : 0;
  return (
    <article className="driver-card">
      <span className="driver-icon" aria-hidden="true">{ICONS[contributor.signal] ?? "•"}</span>
      <div>
        <strong>{contributor.explanation}</strong>
        <div className="muted small">Source: {contributor.source} · observed {new Date(contributor.observed_at).toLocaleDateString()}</div>
        <div className="score-bar" aria-label={`${percentage}% contribution`}><span style={{ width: `${Math.min(100, percentage)}%` }} /></div>
      </div>
      <span className="driver-points">+{contributor.points.toFixed(0)}</span>
    </article>
  );
}
