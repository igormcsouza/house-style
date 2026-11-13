# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/).

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
