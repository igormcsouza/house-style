# Testing standard

| Layer | Tool | Bar |
|---|---|---|
| Python | pytest + pytest-cov | 100% line coverage enforced (`--cov-fail-under=100`) |
| Web frontend | vitest + @testing-library + jsdom + `@vitest/coverage-v8` | `coverage.thresholds: { 100: true }` |
| Expo | jest-expo + testing-library/react-native | `coverageThreshold` 100 |
| Infra | pytest + CDK assertions | in the Python 100% gate |
| End to end | Playwright | REQUIRED when the project has frontend + backend + infra |

## e2e (Playwright)
- Runs against `docker compose up` (the real stack), in CI and locally (`templates/e2e`).
- Projects: desktop Chrome AND a mobile viewport (Pixel 7 / 375px). Same specs, both run.
- Every key flow has: happy path, empty state, error state (API failing), loading skeleton visible.
- Accessibility: `@axe-core/playwright` scan on each main page in light AND dark, zero violations; keyboard-only pass (Tab reaches every control, focus visible); no horizontal overflow at 375px; `prefers-reduced-motion` honored.
- Visual/UX smoke: page has one `h1` and one `main`, images have alt, no console errors, no failed network requests.
- Stable selectors by role/label (`getByRole`), never CSS classes. No sleeps; use auto-waiting assertions.
- Artifacts: traces on first retry, screenshots on failure, uploaded by CI.

## Rules of thumb
- Test behavior, not implementation; one reason to fail per test; fakes over mocks (in-memory repository implementing the Protocol).
- Every bug fix ships a regression test. Coverage is a floor, not the goal: assert outcomes.
