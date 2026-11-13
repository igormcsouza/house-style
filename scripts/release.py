#!/usr/bin/env python3
"""Plan or prepare a release from Conventional Commits. Never pushes, never tags.
  release.py [auto|patch|minor|major] [--apply] [--pre rc] [--notes-out FILE]
Dry run by default. --apply bumps version files, prepends CHANGELOG.md, commits `release: vX.Y.Z` on branch release/vX.Y.Z."""
import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

TAG_RE = r"v[0-9]+\.[0-9]+\.[0-9]+"
CONV = re.compile(r"^(\w+)(\([^)]*\))?(!)?:\s*(.+)$")
SECTIONS = (("Breaking changes", None), ("Added", {"feat"}), ("Changed", {"refactor", "perf", "revert"}), ("Fixed", {"fix"}))
SKIP_DIRS = {"node_modules", ".venv", "venv", ".git", "dist", "build", ".next", "site", "worktrees", "cdk.out"}


def git(*args, cwd="."):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def last_tag(cwd):
    r = subprocess.run(["git", "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*"], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() or None


def commits(cwd, since):
    raw = git("log", f"{since}..HEAD" if since else "HEAD", "--no-merges", "--format=%s%x1f%b%x1e", cwd=cwd)
    out = []
    for rec in filter(None, raw.split("\x1e")):
        subj, _, body = rec.strip().partition("\x1f")
        m = CONV.match(subj.strip())
        if not m or m.group(1) == "release":
            continue
        typ, _, bang, text = m.groups()
        brk = re.search(r"BREAKING[ -]CHANGE:\s*(.+)", body)
        out.append({"type": typ, "breaking": bool(bang or brk), "text": text.strip(), "migration": brk.group(1).strip() if brk else None})
    return out


def bump(cur, kind, cs):
    major, minor, patch = (int(x) for x in cur.split("."))
    brk = any(c["breaking"] for c in cs)
    if kind == "auto":
        releasable = [c for c in cs if c["breaking"] or c["type"] in {"feat", "fix", "perf", "refactor", "revert"}]
        if not releasable:
            return None
        kind = "major" if brk and major >= 1 else "minor" if brk or (major >= 1 and any(c["type"] == "feat" for c in cs)) else "patch"
    if kind == "major":
        return f"{major + 1}.0.0"
    return f"{major}.{minor + 1}.0" if kind == "minor" else f"{major}.{minor}.{patch + 1}"


def notes(cs):
    out = []
    for title, types in SECTIONS:
        if types is None:
            items = [f"- {c['text']}" + (f"\n  Migration: {c['migration']}" if c["migration"] else "") for c in cs if c["breaking"]]
        else:
            items = [f"- {c['text']}" for c in cs if c["type"] in types and not c["breaking"]]
        if items:
            out.append(f"### {title}\n\n" + "\n".join(items))
    return "\n\n".join(out)


def version_files(root):
    """(path, regex with groups (before, version, after)) for every version source found."""
    spec = []
    for rel, rx in (("pyproject.toml", r'(?ms)(^\[project\].*?^version\s*=\s*")([^"]+)(")'),
                    ("package.json", r'(?m)(^\s*"version"\s*:\s*")([^"]+)(")'),
                    ("app.json", r'(?ms)("expo"\s*:\s*\{.*?"version"\s*:\s*")([^"]+)(")'),
                    (".claude-plugin/plugin.json", r'(?m)(^\s*"version"\s*:\s*")([^"]+)(")')):
        if (root / rel).is_file():
            spec.append((root / rel, rx))
    for f in list(root.glob("*/__init__.py")) + list(root.glob("*/*/__init__.py")) + list(root.glob("src/*/__init__.py")):
        if not SKIP_DIRS & set(f.relative_to(root).parts) and "__version__" in f.read_text(errors="ignore"):
            spec.append((f, r"""(__version__\s*=\s*['"])([^'"]+)(['"])"""))
    found = []
    for f, rx in spec:
        m = re.search(rx, f.read_text())
        if m:
            found.append((f, rx, m.group(2)))
    return found


def main():
    a = argparse.ArgumentParser()
    a.add_argument("kind", nargs="?", default="auto", choices=("auto", "patch", "minor", "major"))
    a.add_argument("--apply", action="store_true")
    a.add_argument("--pre", metavar="ID", help="make it a pre-release, e.g. rc -> vX.Y.Z-rc.1")
    a.add_argument("--notes-out")
    a.add_argument("--cwd", default=".")
    a = a.parse_args()
    root = Path(a.cwd).resolve()
    files = version_files(root)
    versions = {v for _, _, v in files}
    tag = last_tag(root)
    if len(versions) > 1:
        sys.exit("version files disagree: " + ", ".join(f"{f.relative_to(root)}={v}" for f, _, v in files))
    base = re.sub(r"-.*$", "", next(iter(versions))) if versions else (tag[1:] if tag else "0.0.0")
    if tag and versions and tag[1:] != next(iter(versions)) and not tag[1:].startswith(next(iter(versions))):
        print(f"note: last tag {tag} != version files {next(iter(versions))} (release PR unmerged or tag drift)")
    cs = commits(root, tag)
    nxt = bump(base, a.kind, cs) if cs else None
    if not nxt:
        sys.exit(f"nothing to release since {tag or 'the first commit'} (only docs/test/ci/chore commits)")
    if not tag:  # first release ships the version already written in the files
        nxt = base if base != "0.0.0" else "0.1.0"
    full = nxt + (f"-{a.pre}.1" if a.pre else "")
    body = notes(cs)
    print(f"last tag: {tag or '(none)'}  ->  v{full}\nfiles: " + (", ".join(str(f.relative_to(root)) for f, _, _ in files) or "(no version file found!)") + f"\n\n{body}\n")
    if a.notes_out:
        Path(a.notes_out).write_text(body + "\n")
    if not a.apply:
        print("dry run. Re-run with --apply to bump files, update CHANGELOG.md and commit on a release branch.")
        return 0
    if git("status", "--porcelain", cwd=root):
        sys.exit("working tree not clean; commit or stash first")
    if git("rev-parse", "--abbrev-ref", "HEAD", cwd=root) in ("main", "master"):
        git("switch", "-c", f"release/v{full}", cwd=root)
    for f, rx, _ in files:
        f.write_text(re.sub(rx, lambda m: m.group(1) + full + m.group(3), f.read_text(), count=1))
    log = root / "CHANGELOG.md"
    head = "# Changelog\n\nFormat based on [Keep a Changelog](https://keepachangelog.com/).\n\n"
    text = log.read_text() if log.is_file() else head
    entry = f"## [{full}] - {datetime.date.today().isoformat()}\n\n{body}\n\n"
    i = text.find("\n## [")
    log.write_text(text[:i + 1] + entry + text[i + 1:] if i >= 0 else text.rstrip("\n") + "\n\n" + entry.rstrip("\n") + "\n")
    git("add", "-A", cwd=root)
    git("commit", "-m", f"release: v{full}", cwd=root)
    print(f"committed release: v{full}. Next (needs user OK): push branch, open PR, merge, then\n"
          f"  gh release create v{full} --target main --title v{full} --notes-file <notes>" + (" --prerelease" if a.pre else ""))
    print("Also refresh lockfiles if the project has them (uv lock / npm install --package-lock-only) before merging.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
