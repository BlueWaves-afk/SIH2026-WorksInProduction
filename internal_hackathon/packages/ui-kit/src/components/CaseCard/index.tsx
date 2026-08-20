import type { AlertCase } from "../../types";
import { BandChip } from "../BandChip";

export function CaseCard({ item, selected = false, onClick }: { item: AlertCase; selected?: boolean; onClick?: () => void }) {
  return (
    <button className={`case-card ${selected ? "selected" : ""}`} onClick={onClick} aria-pressed={selected}>
      <span>
        <strong>{item.village_id}</strong>
        <span className="case-meta"><span>{item.case_id}</span><span>{Math.round(item.confidence * 100)}% confidence</span></span>
      </span>
      <span className="stack" style={{ alignItems: "flex-end", gap: 6 }}><BandChip band={item.band} /><span className="small muted">{item.status}</span></span>
    </button>
  );
}
