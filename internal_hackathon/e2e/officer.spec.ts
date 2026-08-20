import { expect, test } from "@playwright/test";

test("officer can triage and acknowledge a priority case", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Triage" })).toBeVisible();
  await expect(page.getByRole("list", { name: "Ranked complaint queue" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Acknowledge", exact: true })).toBeEnabled();

  await page.getByRole("button", { name: "Acknowledge", exact: true }).click();
  await expect(page.getByText("Acknowledged", { exact: true }).first()).toBeVisible();

  await page.getByRole("button", { name: "Summarize" }).click();
  await expect(page.locator(".geo-map-shell")).toBeVisible();
});
