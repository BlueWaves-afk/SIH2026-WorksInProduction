import type { Band } from "../../types";
import { BAND_LABELS } from "../../types";

export function BandChip({ band }: { band: Band }) {
  return <span className={`band-chip ${band}`}>{BAND_LABELS[band]}</span>;
}
