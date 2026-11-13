# house-style

One UI/UX, accessibility, backend and MCP+OAuth standard for every project, packaged as a Claude Code plugin.
It stays active on every decision Claude makes in an opted-in project and steers it back to the style.

## Install
```
/plugin marketplace add igormcsouza/house-style
/plugin install house-style@house-style
```
Then, inside a project: `/house-style:init`.

### Updates
There is no pinned `version`: every merge to `main` is a new plugin version (commit SHA). Turn on **Enable auto-update** under `/plugin` > Marketplaces > house-style (off by default for third-party marketplaces); it applies after your first message plus up to ~10 minutes, then run `/reload-plugins`. Manual: `/plugin marketplace update house-style` then `claude plugin update house-style@house-style`. To stay on a milestone: `/plugin marketplace add igormcsouza/house-style#v0.1.0`.

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
