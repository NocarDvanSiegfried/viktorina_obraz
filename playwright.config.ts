import { defineConfig, devices } from "@playwright/test"

const useExternalServers = Boolean(process.env.PLAYWRIGHT_NO_WEBSERVER)

export default defineConfig({
  testDir: "e2e/tests",
  timeout: 120_000,
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:5175",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: useExternalServers
    ? undefined
    : [
        {
          command: "python -m uvicorn app.main:app --host 127.0.0.1 --port 8001",
          cwd: "backend",
          url: "http://127.0.0.1:8001/health",
          reuseExistingServer: false,
          timeout: 120_000,
          env: {
            E2E_MOCK_GIGACHAT: "1",
            DATABASE_URL: "sqlite:///./data/e2e_playwright.db",
            FRONTEND_ORIGIN: "http://127.0.0.1:5175",
            GIGACHAT_AUTH_KEY: "",
          },
        },
        {
          command: "npm run dev -- --host 127.0.0.1 --port 5175",
          cwd: "frontend",
          url: "http://127.0.0.1:5175",
          reuseExistingServer: false,
          timeout: 120_000,
          env: {
            VITE_DEV_API_TARGET: "http://127.0.0.1:8001",
          },
        },
      ],
})

// For source-fragments.spec.ts (API-only): same backend port as webServer above.
process.env.PLAYWRIGHT_API_URL ??= "http://127.0.0.1:8001"
