import type { Band } from "../../types";
import { BAND_LABELS } from "../../types";

export function TrafficLightDisc({ band, score }: { band: Band; score?: number }) {
  return (
    <div className={`traffic-light-disc ${band}`} aria-label={`Status: ${BAND_LABELS[band]}`}>
      <span>{BAND_LABELS[band]}{score === undefined ? null : <><br /><strong>{Math.round(score)}</strong>/100</>}</span>
    </div>
  );
}
