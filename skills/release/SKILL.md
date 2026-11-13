---
name: release
description: Cut a new version of the current project - plan the next SemVer from Conventional Commits, bump version files, update CHANGELOG.md, commit on a release branch, then (with the user's OK) PR and GitHub Release. Use when the user runs /house-style:release or asks to cut/ship/publish a version.
disable-model-invocation: true
---

# /house-style:release [auto|patch|minor|major] [--pre rc]

Rules: `${CLAUDE_PLUGIN_ROOT}/rules/releasing.md`. Pushing, merging and creating the GitHub Release are outward-facing: ask the user before each one.

1. Preflight: on a clean tree; `git fetch`; local main up to date; CI green on main (`gh run list --branch main --limit 3`). If not, stop and say why.
2. Dry run: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/release.py <kind> --notes-out <scratchpad>/notes.md`. Show last tag, next version, files, notes. Sanity-check: breaking changes carry a Migration line; notes read as user-facing sentences (edit commits' wording in the CHANGELOG entry if poor); wrong bump -> rerun with an explicit kind.
3. Ask: "Release vX.Y.Z?" (AskUserQuestion). On yes: rerun with `--apply` (creates `release/vX.Y.Z`, bumps every version file, prepends CHANGELOG, commits `release: vX.Y.Z`). Refresh lockfiles (`uv lock`, `npm install --package-lock-only`) and amend the commit.
4. Ask before pushing the branch and opening the PR (title `release: vX.Y.Z (<summary>)`, body = notes). Wait for green CI and the user's merge.
5. After merge, ask before: `gh release create vX.Y.Z --target main --title vX.Y.Z --notes-file <notes>` (`--prerelease` for rc). That creates the tag and triggers delivery.
6. Verify: delivery workflow green (`gh run watch`), release page shows notes, package/Pages updated. Report what shipped and anything unverified.
Never move/delete a published tag; fix forward with a patch. Never publish from the laptop.
