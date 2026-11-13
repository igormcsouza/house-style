# house-style is ACTIVE for this project
Igor's single standard. Apply it to EVERY decision (stack, components, colors, copy of states, auth, API shape),
including when the user does not mention it. If a request conflicts with it, say so in one line and propose the
compliant option; follow the user only if they confirm. Details live in {ROOT}/rules/*.md (ui, a11y, loading, backend, mcp-oauth, docs): read the matching one before deciding.

UI
- Web: Next.js + Tailwind + shadcn/Radix primitives. Mobile: Expo + NativeWind, same tokens. Docs: mkdocs-material.
- Colors ONLY via semantic tokens from house-style.css (bg-background, text-foreground, bg-primary, text-muted-foreground, border-border, destructive, success). Never hex/rgb in components.
- Accent = this project's accent (default green); light AND dark always. Fonts: Geist Sans/Mono. Radius 10px.
- Icons: Lucide only. NEVER emoji, unicode symbols or ASCII art as icons. Project icon lives in brand/ and is used for favicon, apple-icon, app icon, docs logo, README header, empty states.
- No MUI/Emotion/other icon packs. Don't hide scrollbars. Don't remove focus outlines.
- Loading: skeletons for content, inline spinner inside the pressed button for actions, no blocking full-page spinner. Every list/view has loading, empty, error (with retry) and success states.
- A11y floor: WCAG 2.2 AA, keyboard reachable, visible focus, 24px min target (44px touch), alt/aria-label, never color-only state, prefers-reduced-motion respected (already in tokens).

Backend
- FastAPI domain packages (models/exceptions/repositories/services/controllers), env-only config, uv + ruff, 100% test coverage, errors as RFC 9457 problem+json, JSON logs, /healthz.
- MCP: standalone `fastmcp` (`from fastmcp import FastMCP`) + OAuth with auto-discovery (RemoteAuthProvider/OAuthProxy). No hand-rolled .well-known routes.

Project standards (rules/python.md, infra.md, testing.md, security.md)
- Python: uv only (uv.lock, no requirements.txt/Poetry/pip), pytest with 100% coverage enforced, never unittest.TestCase, ruff (templates/python/ruff.toml). Web: vitest with coverage thresholds at 100.
- AWS = CDK in Python only. App runs with `docker compose up`. Every project owns a FIXED port block (scripts/ports.py, range 10000-32759); never the popular defaults (3000, 5000, 8000, 4566, 5432, 8080...). CHANGING an existing project's ports can break sign-in (registered callback/logout URLs, CORS, base URLs): review login first (rules/infra.md) and get the user's OK before redeploying.
- Frontend + backend + infra => Playwright e2e on desktop AND mobile viewport with axe scans, against the compose stack.
- Security: no hard-coded secrets, no CORS `*`, no eval/shell=True/string SQL/pickle, JWT fully validated, problem+json errors. Mobile-first UI, test at 375px.

Docs and releases (rules/docs.md, rules/releasing.md)
- README: icon + H1 + one bold sentence, badges (max 5), Why, Install/Quickstart (tested commands), Usage table, How it works, Docs/Contributing/License. No emoji in headings. <= 200 lines, depth goes to docs/ (mkdocs-material).
- AGENTS.md: Layout, Commands, Conventions, Hard stops, Gotchas; <= 150 lines, only what code cannot say. CLAUDE.md is just `@AGENTS.md`. CONTRIBUTING.md + CHANGELOG.md (Keep a Changelog) + LICENSE (MIT).
- Commits are Conventional Commits with PR number; branches `<type>/<issue>-<kebab>`; squash-merge.
- Versions: SemVer, tags `vX.Y.Z`. Never bump versions or edit CHANGELOG by hand: use `/house-style:release` (it plans from commits, bumps all version files, commits on a release branch). Pushing, merging and `gh release create` need the user's OK. Publish only from a GitHub Release, never from a laptop.

Process
- Docs and code change in the same PR. A hook blocks violating edits. Escape hatch: `house-style: allow <reason>` on that line. Use it rarely.
