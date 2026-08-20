export function Slider({ label, value, min = 0, max = 100, onChange }: { label: string; value: number; min?: number; max?: number; onChange: (value: number) => void }) {
  return <label className="stack" style={{ gap: 6 }}>{label}<input type="range" min={min} max={max} value={value} onChange={(event) => onChange(Number(event.target.value))} /><span className="muted small">{value}</span></label>;
}
