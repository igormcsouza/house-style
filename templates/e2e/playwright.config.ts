import { defineConfig, devices } from "@playwright/test";

// Runs against the REAL stack (docker compose up), on desktop AND a mobile viewport.
const port = process.env.WEB_PORT ?? "{{web_port}}"; // the project's fixed port block (.house-style.json)
const channel = process.env.PW_CHANNEL || undefined; // e.g. "chrome" to reuse a system Chrome locally

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [["html", { open: "never" }], ["list"]],
  use: { baseURL: `http://localhost:${port}`, trace: "on-first-retry", screenshot: "only-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], channel } },
    { name: "mobile", use: { ...devices["Pixel 7"], channel } },
  ],
  webServer: {
    command: "docker compose up --wait",
    url: `http://localhost:${port}`,
    reuseExistingServer: true,
    timeout: 180_000,
  },
});
