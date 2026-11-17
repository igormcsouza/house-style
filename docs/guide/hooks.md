# How it stays active

| Layer | What it does |
|---|---|
| `SessionStart` hook | Injects the [core rules](../standard/core.md) plus the project's accent and icon into every session, also after `/clear` and compaction |
| `UserPromptSubmit` hook | When a prompt touches UI, loading, a11y, auth, API or docs, points Claude to the matching rule page |
| `PreToolUse` guard (`Edit\|Write\|MultiEdit`) | Blocks edits with hard-coded colors, emoji icons, banned icon packs, hidden scrollbars, missing `alt`, removed focus, non-Geist fonts, `mcp.server.fastmcp`, hand-rolled OAuth routes. Claude sees the reason and rewrites |
| Skills | `house-style` (automatic), `init`, `audit`, `release` |

Hooks only act where `.house-style.json` exists, so old projects are untouched until you run `init`. Hooks fail open: an error in a hook never blocks your work.

## Escape hatch

Write `house-style: allow <reason>` on the offending line. Use it rarely; the reason is the record.
