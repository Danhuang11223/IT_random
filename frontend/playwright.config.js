import { defineConfig } from "@playwright/test";

const backendPython = process.env.PLAYWRIGHT_BACKEND_PYTHON || "python";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: `${backendPython} ../manage.py runserver 127.0.0.1:8000 --noreload`,
      url: "http://127.0.0.1:8000/api/health/",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173",
      url: "http://127.0.0.1:5173/login",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
