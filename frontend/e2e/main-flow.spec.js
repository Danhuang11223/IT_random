import { expect, test } from "@playwright/test";

test("login -> generate -> save -> history search/sort", async ({ page }) => {
  await page.goto("/login");

  await page.getByLabel("Username").fill("admin");
  await page.getByLabel("Password").fill("Admin123456!");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Your Suggestion" })).toBeVisible();

  await page.getByRole("button", { name: /Just right/i }).click();
  await page.getByRole("button", { name: /Just me/i }).click();
  await page.getByRole("button", { name: /30 min/i }).click();
  await page.getByRole("button", { name: /Medium \(£15-£50\)/i }).click();
  await page.getByRole("button", { name: /Surprise me/i }).click();

  await expect(
    page.locator(".result-card h3")
  ).toHaveCount(1);

  await page.getByRole("button", { name: /💾 Save|Save/i }).click();
  await expect(page.getByText("Saved for later.")).toBeVisible();

  await page.getByRole("link", { name: "Activity History" }).click();
  await expect(page).toHaveURL(/\/history/);

  await page.getByLabel("Search history").fill("cafe");
  await page.getByRole("button", { name: "Search" }).click();

  await page.getByLabel("Sort").selectOption("oldest");
  await page.getByLabel("Sort").selectOption("title");
  await expect(page.getByRole("heading", { name: "Activity History" })).toBeVisible();
});
