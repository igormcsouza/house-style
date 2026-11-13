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
5. **Scaffold** (deterministic, never overwrites, works without extra permissions because it is a script): `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py <nextjs|expo|mkdocs|fastapi|fastmcp> --css-dir <dir with house-style.css> [--app-dir <next app dir, default app>] [--owner <github owner>] [--repo <repo>]`, run once per folder/stack. It copies the components, root layout (nextjs), `tailwind.config` with the preset (only if none exists), mkdocs config + logo, or the api/mcp tree, and prints created / skipped / notes. Then do what the notes say:
   - nextjs: if the notes say `layout.tsx exists`, patch it as instructed (do not overwrite it); copy `brand/icon.svg` -> `app/icon.svg`, `brand/apple-icon.png` -> `app/apple-icon.png`, `brand/favicon.ico` -> `app/favicon.ico`; install deps from the note (skip if the user said offline); if a tailwind config already existed, add the preset line from the note.
   - expo: `icon` = `brand/icon-1024.png`, adaptive foreground/background from `brand/`, splash with the icon, web favicon = `brand/icon-192.png`; import `house-style.css` in `app/_layout.tsx`.
   - mkdocs: nothing more; verify with `mkdocs build --strict` if installed.
6. **Docs and release files**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py docs --owner <owner> --repo <repo>` creates only what is missing (README, AGENTS.md, CLAUDE.md = `@AGENTS.md`, CONTRIBUTING, CHANGELOG, LICENSE, PR template). If it notes an existing CLAUDE.md, move its content into AGENTS.md. Then fill the remaining `<placeholders>` in README.md/AGENTS.md from the real project (commands, stack, layout); never leave a placeholder. Add `.github/workflows/delivery-pypi.yml` from `${CLAUDE_PLUGIN_ROOT}/templates/release/` for PyPI libraries (fill `<package>`). Fix tags without the `v` prefix only if the user asks.
7. **Verify**: run the project's checks and `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py`; list remaining violations in existing code but do NOT mass-fix them unless asked (adoption is gradual).
8. Report what was created and the 3 commands to preview (dev server, light/dark toggle, keyboard Tab pass).
