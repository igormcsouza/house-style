# Audit

`/house-style:audit [path]` is read-only and works without `.house-style.json`.

| Area | Checks |
|---|---|
| Code | Hard-coded colors, emoji icons, banned UI/icon libs, hidden scrollbars, missing `alt`/focus, fonts; `unittest` in tests |
| Security | CORS `*`, `debug=True`, `verify=False`, `shell=True`, `eval`, string SQL, `pickle`, unsigned JWT, hard-coded secrets |
| Docs and release | README, AGENTS.md, CLAUDE.md, CONTRIBUTING, CHANGELOG, LICENSE, `vX.Y.Z` tags, unpinned plugin version |
| Project | `uv` + `uv.lock`, pytest at 100% coverage, vitest/jest thresholds, FastAPI domain packages, Compose, fixed ports, CDK in Python, Playwright e2e |
| Login after a port change | Lines naming a local port in a login or CORS context (Cognito callbacks, `allow_origins`, base URLs) |

## Flags

| Flag | Effect |
|---|---|
| `--deep` | Also runs ruff (security `S`, complexity, dead code) and pip-audit through uv (needs network) |
| `--workspace ~/Projects` | Detects port collisions across your projects |
| `--ignore dir,dir` | Skip directories |

The result lists counts per rule, worst files and a fix order, cheapest wide wins first. It fixes only when asked, one rule per commit.

!!! warning "Changing ports"
    Moving a project to its fixed port block can break sign-in silently. `scripts/ports.py` lists the login and CORS references first; get an explicit OK before redeploying.
