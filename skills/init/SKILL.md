---
name: init
description: Set up house-style in the current project - pick accent and Lucide icon, generate tokens + icon set (favicon, app icon), copy template components, write AGENTS.md. Use when the user runs /house-style:init or asks to apply the house style to a new or existing project.
disable-model-invocation: true
---

# /house-style:init

Plugin root = `${CLAUDE_PLUGIN_ROOT}`. Do not overwrite existing files without showing the diff first.

1. **Detect stack**: `package.json` has `next` -> nextjs; `expo` -> expo; `mkdocs.yml` -> mkdocs; `fastapi`/`fastmcp` in pyproject -> api / mcp. Several can apply (monorepo): handle each folder.
2. **Ask once** (AskUserQuestion, defaults first): project display name; accent (green default, blue, red, violet, amber, teal); Lucide icon (suggest 3 that fit the project's purpose; user may pick any name from lucide.dev/icons).
3. **Brand**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/brand.py --name "<name>" --icon <lucide-name> --accent <accent> --out brand --stack <stack>`. Writes `brand/*` and `.house-style.json` (the file that switches the guard hooks on).
4. **Tokens** (web/native only): `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/build.py --accent <accent> --out <css dir> --tailwind <3|4>` (check `tailwind` version in package.json). Import `house-style.css` from the global CSS / root layout; add the preset (Tailwind 3) to `tailwind.config`.
5. **Wire per stack** (details in `${CLAUDE_PLUGIN_ROOT}/rules/ui.md`):
   - nextjs: copy `brand/icon.svg` -> `app/icon.svg`, `brand/apple-icon.png` -> `app/apple-icon.png`, `brand/favicon.ico` -> `app/favicon.ico`; Geist fonts via `next/font/google`; `next-themes`; copy `templates/nextjs/*` into `components/` and `app/loading.tsx`; `npx shadcn@latest init` if missing; install `lucide-react`.
   - expo: `icon` = `brand/icon-1024.png`, adaptive foreground/background from `brand/`, splash with the icon, favicon = `brand/icon-192.png`; copy `templates/expo/*`; `nativewind` preset = house-style preset; `lucide-react-native`.
   - mkdocs: copy `templates/mkdocs/mkdocs.yml` values (replace `{{accent}}` with the Material name, `{{name}}`), put `brand/icon.svg` in `docs/assets/`.
   - api: copy `templates/fastapi` layout; mcp: copy `templates/fastmcp`.
6. **Docs and release files** (create only what is missing; show a diff for anything existing, never overwrite silently): `README.md` (`templates/README.md`: fill the placeholders from the real project, use `brand/icon.svg`), `AGENTS.md` (`templates/AGENTS.md`), `CLAUDE.md` containing only `@AGENTS.md` (move any existing CLAUDE.md content into AGENTS.md), `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE` (MIT), `.github/pull_request_template.md` (`templates/release/`). Workflows if missing: `.github/workflows/docs.yml` when the project has mkdocs; `delivery-pypi.yml` for PyPI libraries (fill `<package>`). Fix tags without the `v` prefix only if the user asks.
7. **Verify**: run the project's checks and `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py`; list remaining violations in existing code but do NOT mass-fix them unless asked (adoption is gradual).
8. Report what was created and the 3 commands to preview (dev server, light/dark toggle, keyboard Tab pass).
