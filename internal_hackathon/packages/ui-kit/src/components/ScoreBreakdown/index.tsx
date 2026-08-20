import type { RiskEvent } from "../../types";
import { BandChip } from "../BandChip";
import { DriverPictogramCard } from "../DriverPictogramCard";

export function ScoreBreakdown({ event, title = "Why this status?" }: { event: RiskEvent; title?: string }) {
  const drivers = [...event.contributors].sort((a, b) => b.points - a.points).slice(0, 3);
  return (
    <section className="surface panel" aria-label={title}>
      <div className="row">
        <h2>{title}</h2>
        <span className="spacer" />
        <BandChip band={event.band} />
      </div>
      <p className="muted small">The platform shows the same decision drivers to the farmer and officer. It does not recalculate this result.</p>
      <div className="stack">
        {drivers.map((driver) => <DriverPictogramCard key={`${driver.signal}-${driver.observed_at}`} contributor={driver} />)}
      </div>
      <p className="footer-note">{event.disclaimer} Confidence: {Math.round(event.confidence * 100)}%. Model: {event.model_version}.</p>
    </section>
  );
}
