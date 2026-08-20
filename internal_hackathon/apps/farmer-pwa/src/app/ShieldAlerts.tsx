import { useEffect, useRef, useState } from "react";
import createGlobe from "cobe";
import type { DemoAlert } from "../demo";
import { useT } from "../i18n";

/**
 * Slowly spinning globe (cobe — 5kB WebGL).
 * Warm, low-contrast palette so it reads as ambient backdrop rather than a chart.
 */
function SpinningGlobe({ markers }: { markers: Array<[number, number]> }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState(0);

  useEffect(() => {
    const measure = () => setSize(wrapRef.current?.clientWidth ?? 0);
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  useEffect(() => {
    if (!canvasRef.current || size === 0) return;
    let phi = 0;
    let frame = 0;
    const globe = createGlobe(canvasRef.current, {
      devicePixelRatio: Math.min(window.devicePixelRatio, 2),
      width: size * 2,
      height: size * 2,
      phi: 0,
      theta: 0.22,
      // White sphere + `multiply` blend: the body drops out over the CSS rainbow
      // aura and the map dots remain as soft texture. (cobe has one base colour,
      // so the rainbow has to come from CSS underneath.)
      dark: 0,
      diffuse: 0.3,
      mapSamples: 20000,
      mapBrightness: 2.4,
      baseColor: [1, 1, 1],
      markerColor: [0.93, 0.36, 0.2],
      glowColor: [1, 1, 1],
      opacity: 0.55,
      scale: 1.04,
      markers: markers.map((location) => ({ location, size: 0.05 })),
    });

    // cobe v2 dropped `onRender`; rotation is driven by update() on a rAF loop.
    const tick = () => {
      phi += 0.0022; // slow, ambient drift
      globe.update({ phi });
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);

    return () => { cancelAnimationFrame(frame); globe.destroy(); };
  }, [size, markers]);

  return (
    <div className="shield-globe" ref={wrapRef} aria-hidden="true">
      <span className="shield-globe-aura" />
      <canvas ref={canvasRef} style={{ width: size, height: size }} />
    </div>
  );
}

export function ShieldAlertsScreen({ alerts, onOpenAlert }: { alerts: DemoAlert[]; onOpenAlert: (id: string) => void }) {
  const t = useT();
  return (
    <div className="shield-screen shield-alerts-screen">
      <section className="shield-alerts-intro">
        <h1>{t("alerts.headline")} <em>{t("alerts.headline.accent")}</em></h1>
      </section>

      <SpinningGlobe markers={[[20.2, 73.8], [19.9, 73.6], [20.6, 74.2], [21.1, 75.0]]} />

      <section className="shield-alert-grid" aria-label="Alerts near you">
        {alerts.map((alert) => (
          <button
            key={alert.id}
            className={`shield-alert-tile is-${alert.kind} is-${alert.span}`}
            onClick={() => onOpenAlert(alert.id)}
          >
            <span className="shield-tile-kind">{t(`alerts.kind.${alert.kind}`)}</span>
            {/* Progressive blur: four stacked backdrop layers, each masked to start
                later, so the frost ramps in instead of cutting on a hard edge. */}
            <span className="shield-tile-haze" aria-hidden="true"><i /><i /><i /><i /></span>
            <span className="shield-tile-copy">
              <strong>{alert.title}</strong>
              <small>{alert.meta}</small>
            </span>
          </button>
        ))}
      </section>
    </div>
  );
}
