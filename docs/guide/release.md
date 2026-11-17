# Release

`/house-style:release [auto|patch|minor|major] [--pre rc]`

1. Preflight: clean tree, up-to-date `main`, green CI.
2. Dry run: `scripts/release.py` plans the SemVer bump from Conventional Commits and shows the last tag, next version, files and notes.
3. Bumps every version file, updates `CHANGELOG.md` (Keep a Changelog), commits on a release branch.
4. With your OK for each step: PR, merge, GitHub Release.

Pushing, merging and `gh release create` are outward-facing, so they always ask. Publish only from a GitHub Release, never from a laptop. Never edit versions or the changelog by hand.

See the [releasing rules](../standard/releasing.md).
