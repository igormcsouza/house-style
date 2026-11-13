---
name: house-style
description: Use when building or changing any UI (web, mobile, docs), design tokens, colors, icons, loading/empty/error states, accessibility, a FastAPI backend, an MCP server with OAuth, READMEs/AGENTS.md/docs, Python/uv/pytest/coverage, Docker Compose, ports, AWS CDK, Playwright e2e, security, or versioning and releases in a project that has .house-style.json (or when the user mentions house-style). Applies Igor's single cross-project standard.
---

# house-style

1. Read `${CLAUDE_PLUGIN_ROOT}/rules/core.md`, then the one rule file for the task: `ui.md`, `a11y.md`, `loading.md`, `backend.md`, `mcp-oauth.md`, `docs.md` (README, AGENTS.md, docs site), `python.md` (uv, pytest 100%, ruff), `infra.md` (CDK Python, Compose, fixed ports), `testing.md` (vitest 100%, Playwright e2e), `security.md`, `releasing.md` (commits, versions, cutting a release; use `/house-style:release`).
2. Use the project's `.house-style.json` (name, accent, icon) and `brand/`.
3. Reuse `${CLAUDE_PLUGIN_ROOT}/templates/` instead of inventing components.
4. If the user's request conflicts with the standard, say so in one line, propose the compliant option, proceed only if they confirm.
5. After UI changes run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py` and fix violations.
No `.house-style.json` yet? Offer `/house-style:init`.
