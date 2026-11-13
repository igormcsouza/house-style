# <Project>

<2-3 lines: what it is, the stack.> Follows the house-style standard (plugin `house-style`, config `.house-style.json`: accent, Lucide icon; rules via the plugin hooks).

## Layout
- `<path>`: <only non-obvious places>

## Commands
- Dev: `<cmd>`
- Test: `<cmd>`
- Full check (run before every PR): `<make check | ./scripts/check.sh>`
- Audit house-style: `/house-style:audit`

## Conventions
- Branch `<type>/<issue>-<kebab>` (`feat/`, `bug-fix/`, `ci/`). One PR per slice. Squash-merge with a Conventional Commit title and PR number: `feat(scope): summary (#N)`.
- Tests ship in the same PR; coverage bar: <e.g. 100% backend>.
- UI: semantic tokens, Lucide icons, loading/empty/error states, WCAG 2.2 AA. Backend: FastAPI domain packages. MCP: `fastmcp` + OAuth discovery.
- Docs change in the same PR as behavior. Releases via `/house-style:release`.

## Hard stops (ask the user first)
Deploying, changing prod auth, force push, deleting data, spending money, publishing a release.

## Gotchas
- <non-obvious trap that already burned someone; delete when no longer true>
