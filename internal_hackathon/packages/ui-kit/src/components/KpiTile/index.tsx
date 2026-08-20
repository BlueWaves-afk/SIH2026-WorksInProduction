export function KpiTile({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return <article className="kpi"><div className="kpi-label">{label}</div><div className="kpi-value">{value}</div>{hint ? <div className="muted small">{hint}</div> : null}</article>;
}
