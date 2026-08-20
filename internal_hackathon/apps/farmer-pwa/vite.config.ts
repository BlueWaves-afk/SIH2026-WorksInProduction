import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      // `autoUpdate` + auto-injected registration: no virtual-module import needed.
      registerType: "autoUpdate",
      injectRegister: "auto",
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "Farmer Support",
        short_name: "Support",
        description: "Early crop-support alerts, explained in your language.",
        start_url: "/",
        scope: "/",
        display: "standalone",
        background_color: "#fafbfc",
        theme_color: "#0e8a5f",
        orientation: "portrait",
        icons: [],
      },
      workbox: {
        // Precache the built shell so a cold offline load still boots.
        globPatterns: ["**/*.{js,css,html,webp,woff2}"],
        // MapLibre is a large, route-level enhancement. Fetch/cache it only
        // when the farmer opens a map instead of charging every mobile install.
        globIgnores: ["**/maplibre-gl-*.js"],
        navigateFallback: "index.html",
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: true,
        runtimeCaching: [
          {
            // Status/advisory reads: prefer fresh, fall back to the last good copy.
            urlPattern: ({ url }) => url.pathname.startsWith("/api/v1/"),
            handler: "NetworkFirst",
            options: {
              cacheName: "api-reads",
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 40, maxAgeSeconds: 60 * 60 * 24 * 7 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: ({ request }) => ["image", "font", "style", "script"].includes(request.destination),
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "static-assets",
              expiration: { maxEntries: 80, maxAgeSeconds: 60 * 60 * 24 * 30 },
            },
          },
        ],
      },
      devOptions: { enabled: false },
    }),
  ],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
