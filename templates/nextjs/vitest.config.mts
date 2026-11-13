import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  oxc: { jsx: { runtime: "automatic" } }, // Vite 8 (vitest 5). On Vite <= 7 use esbuild: { jsx: "automatic" }
  resolve: { alias: { "@": path.resolve(__dirname, ".") } },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["**/*.test.{ts,tsx}"],
    exclude: ["e2e/**", "node_modules/**", ".next/**"],
    coverage: {
      provider: "v8",
      include: ["components/**", "lib/**", "app/**"],
      exclude: ["**/*.test.*", "components/ui/**", "app/layout.tsx", "**/*.d.ts"], // components/ui = vendored shadcn
      thresholds: { 100: true }, // 100% lines, branches, functions, statements
    },
  },
});
