# house-style

One UI/UX, accessibility, backend and MCP+OAuth standard for every project, packaged as a Claude Code plugin.
It stays active on every decision Claude makes in an opted-in project and steers it back to the style.

## Install
```
/plugin marketplace add igormcsouza/house-style
/plugin install house-style@house-style
```
1. **Turn on auto-update (once):** `/plugin` > Marketplaces > house-style > **Enable auto-update**. It is off by default for third-party marketplaces; without it you never receive new rules.
2. Inside a project: `/house-style:init`.

### Updates
There is no pinned `version`: every merge to `main` is a new plugin version (its commit SHA), so with auto-update on, changes arrive by themselves after your first message plus up to ~10 minutes; run `/reload-plugins` to apply them in the running session.
- **Manual update:** `/plugin marketplace update house-style`, then `claude plugin update house-style@house-style`. Both are needed: a plain `plugin update` does not refresh the catalog first and reports "already at the latest".
- **Stay on a milestone:** `/plugin marketplace add igormcsouza/house-style#v0.1.0`.
- **Developing the plugin:** add your clone as the marketplace (`/plugin marketplace add ~/Projects/house-style`) to load it in place (edits apply at the next session or `/reload-plugins`), or run `claude --plugin-dir ~/Projects/house-style` for one session.

## What `/house-style:audit` checks
- **Code**: hard-coded colors, emoji icons, banned UI/icon libs, hidden scrollbars, missing `alt`/focus, fonts; security smells (CORS `*`, `debug=True`, `verify=False`, `shell=True`, `eval`, string SQL, `pickle`, JWT without signature, hard-coded secrets); `unittest` in tests.
- **Docs/release**: README, AGENTS.md, CLAUDE.md, CONTRIBUTING, CHANGELOG, LICENSE, `vX.Y.Z` tags, unpinned plugin version.
- **Project**: `uv` + `uv.lock` (no requirements/Poetry), pytest with a 100% coverage gate, vitest/jest thresholds at 100, FastAPI domain packages, `docker compose`, fixed non-default ports without collisions, AWS = CDK in Python, Playwright e2e (mobile viewport + axe) when there is frontend + backend + infra.
- **Login after a port change**: lines in CDK/backend/env/docs that name a local port in a login or CORS context (Cognito callback/logout URLs, `allow_origins`, base URLs). Moving to the fixed block can break sign-in silently, so `scripts/ports.py` lists them before you change anything.
- `--deep`: runs ruff (security `S`, complexity, dead code) and pip-audit through uv. `--workspace ~/Projects`: detects port collisions across your projects.

## How it stays alive
| Layer | What it does |
|---|---|
| `SessionStart` hook | Injects the core rules + the project's accent/icon into every session (also after `/clear` and compaction) |
| `UserPromptSubmit` hook | When a prompt touches UI, loading, a11y, auth, API or docs, points Claude to the matching `rules/*.md` |
| `PreToolUse` guard (`Edit\|Write\|MultiEdit`) | Blocks edits with hard-coded colors, emoji icons, MUI/Emotion/other icon packs, hidden scrollbars, missing `alt`, removed focus, non-Geist fonts, `mcp.server.fastmcp`, hand-rolled OAuth routes. Claude sees the reason and rewrites |
| Skills | `house-style` (auto), `init` (`/house-style:init`), `audit` (`/house-style:audit`), `release` (`/house-style:release`) |
Hooks only act where `.house-style.json` exists, so old projects are untouched until you run `init`. Deliberate exception: `house-style: allow <reason>` on that line.

## What is the standard
- **Look**: neutral zinc + one accent (green default; blue, red, violet, amber, teal), 10px radius, Geist, light + dark, Lucide icons only, project icon (Lucide glyph on accent tile) for favicon / app icon / docs logo.
- **Behavior**: skeletons for content, in-button spinner for actions, loading/empty/error/success for every view, WCAG 2.2 AA, reduced motion.
- **Docs**: README, AGENTS.md (`CLAUDE.md` = `@AGENTS.md`), CONTRIBUTING, CHANGELOG, mkdocs-material; templates for each.
- **Releases**: Conventional Commits, SemVer, `vX.Y.Z` tags; `/house-style:release` plans the bump, updates every version file and the changelog, and stops before anything outward-facing; delivery only from a published GitHub Release.
- **Backend**: FastAPI domain packages, problem+json, 100% coverage. **MCP**: standalone `fastmcp` + OAuth auto-discovery.
Read `rules/`.

## Layout
`rules/` the standard · `lib/` tokens + checks + hygiene · `scripts/` build.py (tokens), brand.py (icons), scaffold.py (templates), audit.py, release.py · `hooks/` · `skills/` · `templates/` (nextjs, expo, fastapi, fastmcp, mkdocs, README/AGENTS/CONTRIBUTING/CHANGELOG, release workflows).

## Develop
`python3 -m unittest discover -s tests -v` (stdlib only). Templates under `templates/fastmcp` and `templates/fastapi` have their own pytest suites (`uv sync && uv run pytest`).
Add an accent: one line in `lib/tokens.py` `ACCENTS` (`python3 scripts/build.py --check` validates contrast).
