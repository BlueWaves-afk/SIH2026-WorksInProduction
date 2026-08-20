import type { ReactNode } from "react";

export function MapWrapper({ title, children }: { title: string; children?: ReactNode }) {
  return <section className="map-placeholder" aria-label={title}><div><strong>{title}</strong><div className="small">Map layer will consume M1's village and mandi coordinates.</div>{children}</div></section>;
}
