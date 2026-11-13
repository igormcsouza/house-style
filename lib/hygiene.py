"""Repo-level docs/release hygiene checks (README, AGENTS.md, CHANGELOG, tags). Stdlib only."""
import json
import re
import subprocess
from pathlib import Path

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⭕️]")
TAG = re.compile(r"^v\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$")


def check_repo(root):
    root = Path(root)
    out = []
    readme = root / "README.md"
    if not readme.is_file():
        out.append("README.md missing (templates/README.md)")
    else:
        t = readme.read_text(errors="ignore")
        heads = [ln for ln in t.splitlines() if ln.startswith("#")]
        if not any(h.startswith("# ") for h in heads):
            out.append("README.md has no H1 title")
        if not any(re.match(r"##\s+(Install|Quickstart|Run locally|Getting started)", h, re.I) for h in heads):
            out.append("README.md has no Install / Quickstart / Run locally section")
        if any(EMOJI.search(h) for h in heads):
            out.append("README.md headings contain emoji (use text only)")
        n = len(t.splitlines())
        if n > 250:
            out.append(f"README.md is {n} lines (target <= 200, move detail to docs/)")
    agents, claude = root / "AGENTS.md", root / "CLAUDE.md"
    if not agents.is_file():
        out.append("AGENTS.md missing (templates/AGENTS.md)")
    elif len(agents.read_text(errors="ignore").splitlines()) > 200:
        out.append("AGENTS.md > 200 lines; keep only what the code cannot say")
    if claude.is_file() and claude.read_text().strip() != "@AGENTS.md":
        out.append("CLAUDE.md should contain only `@AGENTS.md` (move content into AGENTS.md)")
    if not (root / "LICENSE").is_file():
        out.append("LICENSE missing")
    r = subprocess.run(["git", "tag", "--list"], cwd=root, capture_output=True, text=True)
    tags = [t for t in r.stdout.split() if t]
    bad = [t for t in tags if not TAG.match(t)]
    if bad:
        out.append(f"tags not in vX.Y.Z form: {', '.join(bad[:5])}")
    if tags and not (root / "CHANGELOG.md").is_file():
        out.append("CHANGELOG.md missing (released project; `scripts/release.py` creates it)")
    manifest = root / ".claude-plugin" / "plugin.json"
    if manifest.is_file():
        try:
            if "version" in json.loads(manifest.read_text()):
                out.append("plugin.json pins `version`: installed copies only update when it changes. Omit it so every commit is a new version (rules/releasing.md)")
        except ValueError:
            out.append(".claude-plugin/plugin.json is not valid JSON")
    return out
