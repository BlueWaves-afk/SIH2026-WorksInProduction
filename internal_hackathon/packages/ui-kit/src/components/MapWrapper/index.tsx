import type { ReactNode } from "react";

export function MapWrapper({ title, children }: { title: string; children?: ReactNode }) {
  return <section className="map-placeholder" aria-label={title}><div><strong>{title}</strong><div className="small">Village signals and nearby support points</div>{children}</div></section>;
}
