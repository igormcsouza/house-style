"""Repo-level docs/release hygiene checks (README, AGENTS.md, CHANGELOG, tags). Stdlib only."""

import json
import re
import subprocess
from pathlib import Path

EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿⭐⭕️]")
TAG = re.compile(r"^v\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$")
README_MAX_LINES = 250  # reported at 250, the target is 200
AGENTS_MAX_LINES = 200
INSTALL_HEADING = re.compile(r"##\s+(Install|Quickstart|Run locally|Getting started)", re.I)
PINNED = "plugin.json pins `version`: installed copies only update when it changes. Omit it so every commit is a new version (rules/releasing.md)"


def _readme(root):
    readme = root / "README.md"
    if not readme.is_file():
        return ["README.md missing (templates/README.md)"]
    lines = readme.read_text(errors="ignore").splitlines()
    heads = [ln for ln in lines if ln.startswith("#")]
    out = []
    if not any(h.startswith("# ") for h in heads):
        out.append("README.md has no H1 title")
    if not any(INSTALL_HEADING.match(h) for h in heads):
        out.append("README.md has no Install / Quickstart / Run locally section")
    if any(EMOJI.search(h) for h in heads):
        out.append("README.md headings contain emoji (use text only)")
    if len(lines) > README_MAX_LINES:
        out.append(f"README.md is {len(lines)} lines (target <= 200, move detail to docs/)")
    return out


def _agents(root):
    agents, claude = root / "AGENTS.md", root / "CLAUDE.md"
    out = []
    if not agents.is_file():
        out.append("AGENTS.md missing (templates/AGENTS.md)")
    elif len(agents.read_text(errors="ignore").splitlines()) > AGENTS_MAX_LINES:
        out.append("AGENTS.md > 200 lines; keep only what the code cannot say")
    if claude.is_file() and claude.read_text().strip() != "@AGENTS.md":
        out.append("CLAUDE.md should contain only `@AGENTS.md` (move content into AGENTS.md)")
    return out


def _tags(root):
    r = subprocess.run(["git", "tag", "--list"], cwd=root, capture_output=True, text=True)
    tags = [t for t in r.stdout.split() if t]
    out = []
    bad = [t for t in tags if not TAG.match(t)]
    if bad:
        out.append(f"tags not in vX.Y.Z form: {', '.join(bad[:5])}")
    if tags and not (root / "CHANGELOG.md").is_file():
        out.append("CHANGELOG.md missing (released project; `scripts/release.py` creates it)")
    return out


def _plugin_manifest(root):
    manifest = root / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        return []
    try:
        return [PINNED] if "version" in json.loads(manifest.read_text()) else []
    except ValueError:
        return [".claude-plugin/plugin.json is not valid JSON"]


def check_repo(root):
    root = Path(root)
    license_msg = [] if (root / "LICENSE").is_file() else ["LICENSE missing"]
    return _readme(root) + _agents(root) + license_msg + _tags(root) + _plugin_manifest(root)
