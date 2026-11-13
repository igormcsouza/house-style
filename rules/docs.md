# Documentation standard

Write for two readers: a human skimming for 30 seconds, and an agent that has only this repo. Document what code cannot say (why, how to run, what is dangerous). Never restate code.

## Files every repo has
| File | Purpose | Notes |
|---|---|---|
| `README.md` | What it is, why, how to start | Template `templates/README.md`. First screen answers what / why / how to run |
| `AGENTS.md` | Instructions for AI agents (and humans) | Template `templates/AGENTS.md`. `CLAUDE.md` contains only `@AGENTS.md` |
| `CONTRIBUTING.md` | Setup, checks, branch/commit/PR rules | Libraries, plugins, anything public. Template provided |
| `CHANGELOG.md` | Release history | Keep a Changelog; written by `scripts/release.py`, never by hand at release time. See `releasing.md` |
| `LICENSE` | MIT unless told otherwise | |
| `brand/` | Project icon set | From `/house-style:init` |
| `docs/` + `mkdocs.yml` | Docs site | Only when README would exceed ~200 lines or there is a public API |

## README
Order (omit a section only if it does not apply):
1. `# Name` with the project icon (`<img src="brand/icon.svg" width="48" align="left">` or above the title) and ONE bold sentence saying what it is.
2. Badges, max 5, one line: CI, release/package, docs, license. Never decorative.
3. `## Why <Name>?` problem then approach, 3-6 lines. No marketing, no superlatives.
4. `## Install` or `## Quickstart` (libs/CLIs) or `## Run locally` (apps): copy-paste commands that work first try. Test them.
5. `## Usage` / `## Commands`: a table beats prose. Show real output once.
6. `## How it works`: one mermaid diagram or short list. Link deeper docs instead of growing the README.
7. Apps only: `## Quality gates`, `## Deploy`.
8. `## Documentation` link, `## Contributing` link, `## License`.
Rules: headings are text only (no emoji, no ASCII art); code fences always carry a language; relative links; no secrets or personal data; no stale screenshots (prefer text); target <= 200 lines, move the rest to `docs/`; README is updated in the same PR as the behavior it describes.

## AGENTS.md
The agent's operating manual. Only what it cannot derive from the code, imperative, <= 150 lines.
Sections, in this order:
1. `# <Project>` + 2-3 lines: what it is and the stack.
2. `## Layout`: where things live (only non-obvious paths).
3. `## Commands`: exact one-liners for dev, test, lint, full check (`make check`/`./scripts/check.sh`).
4. `## Conventions`: branch `<type>/<issue>-<kebab>`, Conventional Commits, one PR per slice, tests/coverage bar, house-style pointer.
5. `## Hard stops`: actions needing the user's explicit OK (deploy, prod auth, force push, deleting data, spending money).
6. `## Gotchas`: traps that already burned someone (version quirks, env needs, flaky areas). Add a line when a bug teaches something; delete lines that stop being true.
Nested `AGENTS.md` in a subfolder only when its rules truly differ (e.g. `frontend/`). No duplicated README prose, no secrets, no task lists (use issues).

## Code docs
- Comment the why and the non-obvious constraint, never the what. Delete comments that restate code.
- Public functions/classes: one-line docstring minimum (Python), TSDoc on exported API of libraries.
- Decisions with lasting consequences: `docs/decisions/NNNN-title.md` (Context, Decision, Consequences, 10-20 lines).
- Errors say what happened and what to do next. CLI `--help` is documentation; keep it accurate.

## Docs site (mkdocs-material)
Use `templates/mkdocs/mkdocs.yml`. Palette: both schemes with toggle, `primary`/`accent` = project accent as a Material color (green, blue, red, deep purple, amber, teal). `theme.logo` and `theme.favicon` = `docs/assets/icon.svg` (from `brand/icon.svg`). Keep Material's default font. Features: navigation.tabs, navigation.sections, navigation.top, search.highlight, content.code.copy. No emoji in nav or headings. Build with `mkdocs build --strict` in CI; deploy to GitHub Pages on push to main (`templates/release/docs.yml`).
Structure: `docs/index.md` (what/why/start), `docs/guide/` (tasks), `docs/reference/` (API/CLI/config), `docs/project/` (architecture, testing, decisions).
