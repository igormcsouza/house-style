# Versioning and releases

## Conventions (already how your repos work, now enforced)
- **SemVer, tags `vX.Y.Z`** (always the `v`). Stay on `0.x` until the public contract is stable, then `1.0.0`.
  - `0.x`: breaking change -> bump minor; everything else (features, fixes) -> bump patch.
  - `>= 1.0`: breaking -> major, `feat` -> minor, everything else -> patch.
  - Pre-releases `vX.Y.Z-rc.N` are published as GitHub *pre-releases* (delivery skips them).
- **Conventional Commits**, subject <= 72 chars, imperative, PR number appended: `feat(router): opt-in claude harness (#5)`.
  Types: `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`. Breaking = `!` after type (`feat!:`) and/or a `BREAKING CHANGE:` footer saying how to migrate.
- Branches `<type>/<issue>-<kebab>` (`feat/12-oauth-login`, `bug-fix/9-null-title`, `ci/...`). One PR per slice, squash-merge with the conventional title, `Refs #N`/`Closes #N`.
- **One version source per project** (pyproject `version`, `package.json`, `app.json`, `__version__`, `plugin.json` - all kept equal by `release.py`).
- `CHANGELOG.md` (Keep a Changelog) is generated from commits at release time; the same section is the GitHub Release body.

## Release notes format
Sections in this order, only non-empty ones: `### Breaking changes` (each with a Migration line), `### Added`, `### Changed`, `### Fixed`. Bullets are user-facing sentences with the issue/PR refs. No `chore/docs/test/ci` noise.

## How to cut a version
Use `/house-style:release [patch|minor|major]` (default: auto from commits). It runs `scripts/release.py`:
1. Dry run: shows last tag, next version, files to bump, and the notes. Nothing changes.
2. `--apply`: bumps every version file, prepends the CHANGELOG section, commits `release: vX.Y.Z (<summary>)` on a `release/vX.Y.Z` branch. It never pushes or tags.
3. Open a PR for that commit; CI must be green; merge it.
4. From updated `main`: `gh release create vX.Y.Z --target main --title vX.Y.Z --notes-file <notes>` (add `--prerelease` for rc). Creating the GitHub Release creates the tag and triggers delivery.
Steps 3-4 are outward-facing: confirm with the user before each.

## Delivery
- **Libraries/CLIs (PyPI/npm)**: publish ONLY from a published GitHub Release (`templates/release/delivery-pypi.yml`): tag must equal the package version, pre-releases skipped, PyPI trusted publishing via OIDC (no stored secrets), sdist+wheel attached to the release.
- **Apps (AWS)**: deploy workflows run from `main`/tag; prod deploys need the user's OK (hard stop). Mobile builds: `mobile-release` workflow on tag.
- **Plugins**: version in `.claude-plugin/plugin.json` is the release; users update with `/plugin update`.
- **Docs**: Pages deploy on push to `main` (`templates/release/docs.yml`).
Never move or delete a published tag; ship a new patch instead. Never publish from a laptop.
