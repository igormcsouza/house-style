# house-style

Claude Code plugin: one UI/UX, a11y, backend, MCP+OAuth, docs and release standard for all of Igor's projects. Python stdlib only (hooks, scripts, lib); templates carry their own deps. Follows its own standard.

## Layout
- `rules/`: the standard (core.md is injected every session; the rest is read on demand).
- `lib/`: `tokens.py` (accents, contrast, CSS/preset), `checks.py` (per-file violation + security rules), `hygiene.py` (repo docs/release checks), `project.py` (uv, pytest/vitest 100%, FastAPI layout, Compose, ports, CDK, e2e, login/CORS port refs), `ports.py` (fixed port blocks), `cfg.py`.
- `hooks/`: SessionStart, UserPromptSubmit, PreToolUse guard. `scripts/`: build.py, brand.py, scaffold.py, ports.py, audit.py (`--deep`, `--workspace`), release.py. `skills/`: house-style, init, audit, release. `templates/`: scaffolds.

## Commands
- Everything: `uv sync && uv run ruff check . && uv run ruff format --check . && uv run pytest` (pytest enforces 100% coverage) and `claude plugin validate .`
- Self-audit: `python3 scripts/audit.py . --ignore templates`
- Templates (own projects): `cd templates/<fastmcp|fastapi|cdk> && uv sync && uv run pytest && uv run ruff check --config ../python/ruff.toml .`
- New accent: one line in `lib/tokens.py` `ACCENTS`, then `python3 scripts/build.py --check`.

## Conventions
- Conventional Commits, `feat/...` branches, releases via `scripts/release.py` (never hand-edit versions or CHANGELOG).
- A new rule needs: text in `rules/`, a check in `lib/checks.py` (per file) or `lib/project.py` (per project) when machine-checkable, and a test. Tests are pytest only, in-process (so coverage sees them), hermetic (no network; fake external tools). Keep `rules/core.md` short: it costs tokens every session.
- Hooks must never crash or block on their own errors (fail open).
- `plugin.json` has NO `version` on purpose: every commit on main is a new plugin version (commit SHA). Do not add one; hygiene flags it.

## Hard stops (ask first)
Publishing the repo/releases, changing the default accent or the standard's bans, anything that touches the user's other projects (including their ports or login callback URLs).

## Gotchas
- Hooks only act in projects with `.house-style.json`; keep it that way so old projects are not harassed.
- `.mdx` is content, not UI: not scanned. Python test files are only checked for `unittest`. The detector's own rule text carries `house-style: allow` markers.
- ruff runs with the house config (`ruff.toml` extends `templates/python/ruff.toml`); CLI/hook exceptions are listed there with reasons.
- Verify FastMCP auth docs (https://gofastmcp.com/servers/auth/authentication) when upgrading; the template tests pin the behavior.
