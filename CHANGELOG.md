# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [0.2.0] - 2026-11-13

The audit now covers your project standards, not just UI snippets, and every port change reviews login first.

### Added

- **Project audit** (`/house-style:audit`): `uv` only (`uv.lock`, no requirements/Poetry), pytest with a 100% coverage gate and no `unittest`, vitest/jest coverage thresholds at 100, FastAPI domain-package layout, Docker Compose required, fixed non-default ports without collisions, AWS means CDK in Python, and Playwright e2e (mobile viewport + axe) when there is frontend + backend + infra.
- **Security and smells**: Python checks for CORS `*`, `debug=True`, `verify=False`, `shell=True`, `eval`, string-built SQL, `pickle`, JWT without signature verification and hard-coded secrets. `--deep` runs ruff (bandit `S` rules, complexity, dead code) and pip-audit through uv; `--workspace` detects port collisions across your projects.
- **Fixed port blocks** (`scripts/ports.py`): each project owns 10 consecutive ports inside 10000-32759 (below the Linux ephemeral range), derived from its name, collision-aware, stored in `.house-style.json`.
- **Login-aware port changes**: moving ports can silently break Cognito/OAuth sign-in. The audit and `ports.py` list every login/CORS line that still names a local port (callback and logout URLs, `allow_origins`, base URLs) before anything changes, and the rules, init skill and AGENTS template make it a hard stop.
- **Rules**: `python.md`, `infra.md`, `testing.md`, `security.md`; core rules and prompt routing updated.
- **Templates** (all verified): vitest config and component tests, Playwright e2e (desktop + mobile, axe in light and dark), Docker Compose with non-root Dockerfiles, CDK Python starter, Python tooling with the house ruff config. `scaffold.py` gains `docker`, `e2e`, `python`, `cdk`.

### Changed

- The plugin no longer pins `version`: every commit on `main` is a new version (its commit SHA). Turn on marketplace auto-update to receive changes; the audit flags a pinned plugin version.
- `release.py` works from the git tag when there is no version file and ignores non-packaged dev projects.
- This repository follows its own standard: pytest with 100% coverage enforced (212 tests), house ruff config, `uv.lock` committed, and CI running lint, format, tests, self-audit and the template suites.

### Fixed

- `brand.py` keeps existing `.house-style.json` keys (such as `ports`) when re-run.
- Compose scanning is fast (pruned walk) and understands inline `ports: [...]` lists.
- The first release ships the version already written in the files; Lucide icons with compact SVG arc flags render.

## [0.1.0] - 2026-11-13

First release. One UI/UX, accessibility, backend, MCP+OAuth, docs and release standard for every project, as a Claude Code plugin that stays active on every decision.

### Added

- **Always-on steering**: SessionStart hook injects the core rules and the project's accent/icon; UserPromptSubmit routes UI, a11y, auth, API, docs and release prompts to the matching rule file; PreToolUse guard blocks hard-coded colors, emoji icons, MUI/Emotion and other icon packs, hidden scrollbars, missing alt text, removed focus outlines, non-Geist fonts, `mcp.server.fastmcp` and hand-rolled OAuth routes. Opt-in per project through `.house-style.json`; `house-style: allow <reason>` is the escape hatch.
- **Design tokens**: zinc neutrals plus six contrast-validated accents (green default, blue, red, violet, amber, teal) for light and dark; Tailwind 3 preset, Tailwind 4 `@theme`, NativeWind.
- **Project icon**: a Lucide glyph on an accent tile, generated as SVG, PNG set, `favicon.ico` and Android adaptive icon.
- **Skills**: `/house-style:init` (brand, tokens, scaffolds, docs files), `/house-style:audit` (code violations and docs/release hygiene), `/house-style:release` (SemVer from Conventional Commits, version files, CHANGELOG, release branch; never pushes or tags), plus the auto-loaded `house-style` skill.
- **Rules** for UI, accessibility (WCAG 2.2 AA), loading/empty/error states, FastAPI backend, FastMCP with OAuth auto-discovery, documentation (README, AGENTS.md, mkdocs) and releases.
- **Templates**: Next.js and Expo components, FastAPI (problem+json, 100% coverage), FastMCP with OAuth discovery, mkdocs, README/AGENTS/CONTRIBUTING/CHANGELOG, PyPI delivery and Pages workflows.
- CI: plugin tests, self-audit and template suites.

### Fixed

- First release now ships the version already written in the files instead of bumping past it.
- Icon generation no longer fails on Lucide icons with compact SVG arc flags (such as `leaf`).
- `init` scaffolding is deterministic and works under restricted permissions; Tailwind 4 and existing layouts are handled.
