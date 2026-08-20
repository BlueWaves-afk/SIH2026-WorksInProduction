import { defineConfig, devices } from "@playwright/test";

const demoEnvironment = {
  VITE_AUTH_REQUIRED: "false",
  VITE_DEMO_MODE: "true",
  VITE_API_BASE_URL: "http://127.0.0.1:9/api/v1",
  VITE_MAP_STYLE_URL: "https://tiles.openfreemap.org/styles/liberty",
};

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "farmer-mobile",
      testMatch: /farmer\.spec\.ts/,
      use: { ...devices["Pixel 7"], baseURL: "http://127.0.0.1:5173" },
    },
    {
      name: "officer-desktop",
      testMatch: /officer\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], baseURL: "http://127.0.0.1:5174" },
    },
  ],
  webServer: [
    {
      command: "npm run dev:farmer -- --host 127.0.0.1",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      env: demoEnvironment,
    },
    {
      command: "npm run dev:officer -- --host 127.0.0.1",
      url: "http://127.0.0.1:5174",
      reuseExistingServer: !process.env.CI,
      env: demoEnvironment,
    },
  ],
});
