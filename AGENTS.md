# house-style

Claude Code plugin: one UI/UX, a11y, backend, MCP+OAuth, docs and release standard for all of Igor's projects. Python stdlib only (hooks, scripts, lib); templates carry their own deps. Follows its own standard.

## Layout
- `rules/`: the standard (core.md is injected every session; the rest is read on demand).
- `lib/`: `tokens.py` (accents, contrast, CSS/preset), `checks.py` (violation rules), `hygiene.py` (repo docs/release checks), `cfg.py`.
- `hooks/`: SessionStart, UserPromptSubmit, PreToolUse guard. `scripts/`: build.py, brand.py, audit.py, release.py. `skills/`: house-style, init, audit, release. `templates/`: scaffolds.

## Commands
- Check everything: `python3 -m unittest discover -s tests` and `claude plugin validate .`
- Templates: `cd templates/fastmcp && uv sync && uv run pytest`; same for `templates/fastapi`.
- Self-audit: `python3 scripts/audit.py .`
- New accent: one line in `lib/tokens.py` `ACCENTS`, then `python3 scripts/build.py --check`.

## Conventions
- Conventional Commits, `feat/...` branches, releases via `scripts/release.py` (never hand-edit versions or CHANGELOG).
- A new rule needs: text in `rules/`, a check in `lib/checks.py` when machine-checkable, and a test. Keep `rules/core.md` short: it costs tokens every session.
- Hooks must never crash or block on their own errors (fail open).

## Hard stops (ask first)
Publishing the repo/releases, changing the default accent or the standard's bans, anything that touches the user's other projects.

## Gotchas
- Hooks only act in projects with `.house-style.json`; keep it that way so old projects are not harassed.
- `.mdx` is content, not UI: not scanned. Test files are exempt from Python checks.
- Verify FastMCP auth docs (https://gofastmcp.com/servers/auth/authentication) when upgrading; the template tests pin the behavior.
