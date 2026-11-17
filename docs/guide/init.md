# Init a project

`/house-style:init` detects the stack (Next.js, Expo, mkdocs, FastAPI, FastMCP), asks once for a display name, an accent and a Lucide icon, then:

- generates the design tokens and the icon set in `brand/` (favicon, app icon, docs logo);
- copies the matching [templates](../project/contributing.md#templates);
- writes `AGENTS.md` and `.house-style.json`.

It never overwrites an existing file without showing the diff first.

## Accents

`green` (default), `blue`, `red`, `violet`, `amber`, `teal`. Every accent is contrast-checked for light and dark.

## Scaffold one piece

```bash
python3 scripts/scaffold.py mkdocs --dest . --name my-app --accent green
```

Stacks: `nextjs`, `expo`, `mkdocs`, `fastapi`, `fastmcp`, `docker`, `e2e`, `python`, `cdk`, `docs`. Existing files are skipped, never overwritten.
