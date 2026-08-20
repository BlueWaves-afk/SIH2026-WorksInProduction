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
