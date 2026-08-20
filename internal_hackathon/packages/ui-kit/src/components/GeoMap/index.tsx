import { useEffect, useRef, useState } from "react";
import type { Map as MapLibreMap, Marker as MapLibreMarker } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export interface GeoMapPoint {
  id: string;
  label: string;
  longitude: number;
  latitude: number;
  tone?: "blue" | "green" | "amber" | "red" | "current";
  detail?: string;
}

export interface GeoMapProps {
  points: GeoMapPoint[];
  center: [number, number];
  zoom?: number;
  styleUrl?: string;
  label: string;
  privacyNote?: string;
}

const DEFAULT_STYLE = "https://tiles.openfreemap.org/styles/liberty";

/** Interactive MapLibre surface for public or deliberately coarse locations. */
export function GeoMap({ points, center, zoom = 9, styleUrl = DEFAULT_STYLE, label, privacyNote }: GeoMapProps) {
  const container = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!container.current) return;
    let disposed = false;
    let map: MapLibreMap | null = null;
    const markers: MapLibreMarker[] = [];
    void import("maplibre-gl").then(({ LngLatBounds, Map, Marker, NavigationControl, Popup }) => {
      if (disposed || !container.current) return;
      try {
        const activeMap = new Map({ container: container.current, style: styleUrl, center, zoom, attributionControl: { compact: true } });
        map = activeMap;
        activeMap.addControl(new NavigationControl({ showCompass: false }), "top-right");
        activeMap.on("load", () => {
          if (disposed || points.length < 2) return;
          const bounds = new LngLatBounds();
          points.forEach((point) => bounds.extend([point.longitude, point.latitude]));
          activeMap.fitBounds(bounds, { padding: 48, maxZoom: 11, duration: 0 });
        });
        activeMap.on("error", () => { if (!activeMap.loaded()) setFailed(true); });
        points.forEach((point) => {
          const markerElement = document.createElement("button");
          markerElement.type = "button";
          markerElement.className = `geo-map-marker tone-${point.tone ?? "blue"}`;
          markerElement.setAttribute("aria-label", point.label);
          markerElement.title = point.label;
          const popup = new Popup({ offset: 18, closeButton: false }).setText(point.detail ? `${point.label} — ${point.detail}` : point.label);
          markers.push(new Marker({ element: markerElement, anchor: "center" }).setLngLat([point.longitude, point.latitude]).setPopup(popup).addTo(activeMap));
        });
      } catch {
        setFailed(true);
      }
    }).catch(() => setFailed(true));
    return () => {
      disposed = true;
      markers.forEach((marker) => marker.remove());
      map?.remove();
    };
  }, [center, points, styleUrl, zoom]);

  return (
    <section className="geo-map-shell" aria-label={label}>
      {failed ? <div className="geo-map-fallback">Map tiles are temporarily unavailable.</div> : <div ref={container} className="geo-map-canvas" />}
      {privacyNote && <span className="geo-map-privacy">{privacyNote}</span>}
    </section>
  );
}
