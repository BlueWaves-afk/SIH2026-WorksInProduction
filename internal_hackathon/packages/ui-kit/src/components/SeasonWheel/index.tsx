import { IconPicker } from "../IconPicker";

const OPTIONS = [
  { value: "kharif", label: "Kharif", icon: "🌧️" },
  { value: "rabi", label: "Rabi", icon: "🌤️" },
  { value: "zaid", label: "Zaid", icon: "☀️" },
] as const;

export function SeasonWheel({ value, onChange }: { value?: (typeof OPTIONS)[number]["value"]; onChange: (value: (typeof OPTIONS)[number]["value"]) => void }) {
  return <IconPicker label="Sowing season" options={[...OPTIONS]} value={value} onChange={onChange} />;
}
