export function ConsentToggle({ label, description, value, onChange }: { label: string; description: string; value: boolean; onChange: (value: boolean) => void }) {
  return (
    <div className="check-row">
      <div><strong>{label}</strong><div className="muted small">{description}</div></div>
      <button className="toggle" type="button" aria-pressed={value} aria-label={`${label}: ${value ? "on" : "off"}`} onClick={() => onChange(!value)} />
    </div>
  );
}
