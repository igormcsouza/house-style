# house-style

**One UI/UX, accessibility, backend, MCP+OAuth, docs and release standard for every project, packaged as a Claude Code plugin.**

## Why

Every new project drifts: a different green, emoji icons, a new auth flow, no tests. house-style keeps one standard and makes Claude follow it on each decision, so projects look and behave alike without re-explaining the rules.

## How

1. [Install](getting-started/install.md) the plugin once.
2. Run `/house-style:init` in a project: it picks an accent and icon, generates tokens and the icon set, and writes `.house-style.json`.
3. From then on hooks inject the [standard](standard/core.md) into every session and block edits that break it.
4. [Audit](guide/audit.md) any repo to see how far it is, and [release](guide/release.md) with one command.

Projects without `.house-style.json` are never touched.

## Where to go next

<div class="grid cards" markdown>

- **[Install](getting-started/install.md)**: two commands and auto-update.
- **[Guide](guide/index.md)**: init, audit, release.
- **[The standard](standard/core.md)**: every rule, one page per area.
- **[Contributing](project/contributing.md)**: add a rule or an accent.

</div>
