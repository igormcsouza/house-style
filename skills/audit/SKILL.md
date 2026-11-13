---
name: audit
description: Audit the current repo (or a path) against house-style - hard-coded colors, emoji icons, banned UI libs, hidden scrollbars, missing alt/focus, wrong fonts, non-fastmcp MCP/OAuth. Use when the user runs /house-style:audit or asks how far a project is from the standard.
disable-model-invocation: true
---

# /house-style:audit

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py [path]` (read-only; works without `.house-style.json`).
2. Summarize: counts per rule, worst files, the docs/release hygiene findings (README, AGENTS.md, CLAUDE.md, CHANGELOG, LICENSE, `vX.Y.Z` tags), and what is NOT machine-checkable (see checklist below).
3. Propose a fix order (cheapest wide wins first: tokens/colors, icons, banned libs). Fix only if asked; if asked, do one rule per commit.

Manual checklist the script cannot see: loading/empty/error states per view, keyboard pass, 200% zoom, light+dark both present, project icon used for favicon/app icon/docs logo, FastAPI layout and problem+json, MCP auth provider choice, README accuracy (commands really run), AGENTS.md gotchas still true.
