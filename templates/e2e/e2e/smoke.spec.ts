import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const PAGES = ["/"]; // list every main route

for (const scheme of ["light", "dark"] as const) {
  for (const path of PAGES) {
    test(`${path} has no accessibility violations (${scheme})`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: scheme, reducedMotion: "reduce" });
      await page.goto(path);
      const { violations } = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag22aa"]).analyze();
      expect(violations).toEqual([]);
    });
  }
}

for (const path of PAGES) {
  test(`${path} structure: one h1, one main, alt on images, no horizontal overflow`, async ({ page }) => {
    await page.goto(path);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("main")).toHaveCount(1);
    expect(await page.locator("img:not([alt])").count()).toBe(0);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0); // fails on 375px if anything is wider than the screen
  });

  test(`${path} keyboard: Tab lands on a visible focus target`, async ({ page, isMobile }) => {
    test.skip(isMobile, "no hardware keyboard on the mobile project");
    await page.goto(path);
    await page.keyboard.press("Tab");
    const focused = page.locator(":focus-visible");
    await expect(focused).toHaveCount(1);
    await expect(focused).toBeVisible();
  });

  test(`${path} has no console errors or failed requests`, async ({ page }) => {
    const problems: string[] = [];
    page.on("console", (m) => m.type() === "error" && problems.push(m.text()));
    page.on("requestfailed", (r) => problems.push(`${r.method()} ${r.url()}`));
    await page.goto(path, { waitUntil: "networkidle" });
    expect(problems).toEqual([]);
  });
}
