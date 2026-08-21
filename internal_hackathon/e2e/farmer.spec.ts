import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("farmer-onboarded", "true");
    window.localStorage.setItem("kisansetu.farmer_token", "farmer-demo-token");
  });
});

test("farmer can review status and open nearby markets on mobile", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Cotton Stress Alert", { exact: false })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Farmer navigation" })).toBeVisible();

  await page.getByRole("button", { name: "Nearby markets" }).click();
  await expect(page.getByRole("heading", { name: "Nearby markets" })).toBeVisible();
  await expect(page.getByText("Markets near you")).toBeVisible();
  await expect(page.locator(".geo-map-shell")).toBeVisible();
});

test("copilot exposes voice capture and playback controls", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Ask support copilot" }).evaluate((element) => (element as HTMLButtonElement).click());
  await expect(page.getByRole("button", { name: "Record a voice question" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Play the answer aloud" })).toBeEnabled();

  // The test browser has no microphone grant. The UI must fail safely and
  // leave the text composer usable instead of trapping the farmer.
  await page.getByRole("button", { name: "Record a voice question" }).click();
  await expect(page.getByRole("alert")).toContainText(/microphone|recording/i);
  await expect(page.getByRole("textbox", { name: /ask|question/i })).toBeEnabled();
});

test("copilot sends a microphone recording and plays a synthesized answer", async ({ page }) => {
  const transcribeBodies: string[] = [];
  const synthesizeBodies: string[] = [];

  await page.addInitScript(() => {
    class FakeMediaRecorder {
      static isTypeSupported() { return true; }
      state = "inactive";
      mimeType = "audio/webm;codecs=opus";
      ondataavailable: ((event: { data: Blob }) => void) | null = null;
      onstop: (() => void) | null = null;
      constructor(_stream: MediaStream, _options?: MediaRecorderOptions) {}
      start() {
        this.state = "recording";
        this.ondataavailable?.({ data: new Blob(["mock-audio"], { type: "audio/webm" }) });
      }
      stop() {
        this.state = "inactive";
        this.onstop?.();
      }
    }
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) },
    });
    Object.defineProperty(window, "MediaRecorder", { configurable: true, value: FakeMediaRecorder });
    class FakeAudio {
      onended: (() => void) | null = null;
      onerror: (() => void) | null = null;
      constructor(_url: string) {}
      play() { return Promise.resolve(); }
      pause() {}
    }
    Object.defineProperty(window, "Audio", { configurable: true, value: FakeAudio });
  });
  await page.route("**/api/v1/copilot/speech/transcribe", async (route) => {
    transcribeBodies.push(route.request().postData() ?? "");
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ text: "How should I protect my cotton crop?", language_code: "en-IN", confidence: 0.98, provider: "sarvam" }) });
  });
  await page.route("**/api/v1/copilot/speech/synthesize", async (route) => {
    synthesizeBodies.push(route.request().postData() ?? "");
    await route.fulfill({ status: 200, contentType: "audio/wav", body: Buffer.from("RIFFmock-audio") });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Ask support copilot" }).evaluate((element) => (element as HTMLButtonElement).click());
  await page.getByRole("button", { name: "Record a voice question" }).click();
  await expect(page.getByRole("button", { name: "Stop recording" })).toBeVisible();
  await page.getByRole("button", { name: "Stop recording" }).evaluate((element) => (element as HTMLButtonElement).click());
  await expect.poll(() => transcribeBodies.length).toBe(1);
  await expect(page.getByRole("textbox", { name: /ask|question/i })).toHaveValue("How should I protect my cotton crop?");
  expect(JSON.parse(transcribeBodies[0]).audio_base64).toContain("data:audio/webm");

  await page.getByRole("button", { name: "Play the answer aloud" }).evaluate((element) => (element as HTMLButtonElement).click());
  await expect(page.getByRole("button", { name: "Stop playback" })).toBeVisible();
  await expect.poll(() => synthesizeBodies.length).toBe(1);
  expect(JSON.parse(synthesizeBodies[0]).text).toContain("Hello");
});
