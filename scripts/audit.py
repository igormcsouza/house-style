#!/usr/bin/env python3
"""Audit a repo against house-style. Read-only. Usage: audit.py [path] ; exit 1 if violations."""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import checks
import hygiene
import project

FIX_COLUMN = 3  # pip-audit table: name, version, id, fix
SKIP = {
    "node_modules",
    ".next",
    "out",
    ".git",
    "cdk.out",
    "dist",
    "build",
    ".venv",
    "venv",
    "worktrees",
    "__pycache__",
    "coverage",
    "playwright-report",
    "test-results",
    ".expo",
    "android",
    "ios",
    "site",
}
EXT = checks.UI_EXT | {".py"}


def deep(root, ignore):
    """Optional: run real tools. ruff (security S, smells C901/PLR/ERA) and pip-audit via uvx. Skipped if uv is missing."""
    uv = shutil.which("uv")
    if not uv:
        return ["--deep needs uv (https://docs.astral.sh/uv/)"]
    out, ruff_cfg = [], Path(__file__).resolve().parent.parent / "templates" / "python" / "ruff.toml"
    for d, files in project.walk(root, ignore=ignore):
        if "pyproject.toml" not in files:
            continue
        rel = d.relative_to(root) or Path(".")
        r = subprocess.run(
            [
                uv,
                "tool",
                "run",
                "ruff",
                "check",
                "--config",
                str(ruff_cfg),
                "--no-cache",
                "--output-format",
                "concise",
                str(d),
            ],
            capture_output=True,
            text=True,
        )
        lines = [ln.replace(str(root) + "/", "") for ln in r.stdout.splitlines() if re.match(r".+:\d+:\d+: ", ln)]
        out += [f"ruff {ln}" for ln in lines if re.search(r": S\d+ ", ln)]  # security findings are always listed
        by_code = Counter(re.search(r": ([A-Z]+\d+) ", ln).group(1) for ln in lines if re.search(r": ([A-Z]+\d+) ", ln))
        top = ", ".join(f"{c} x{n}" for c, n in by_code.most_common(8))
        out += [f"ruff {rel}: {len(lines)} finding(s), top: {top}"] if lines else []
        if "uv.lock" in files:
            with tempfile.TemporaryDirectory() as t:
                req = Path(t) / "req.txt"
                e = subprocess.run(
                    [uv, "export", "--frozen", "--no-hashes", "--no-emit-project", "-o", str(req)],
                    cwd=d,
                    capture_output=True,
                    text=True,
                )
                if e.returncode == 0:
                    a = subprocess.run(
                        [uv, "tool", "run", "pip-audit", "-r", str(req), "--no-deps", "--disable-pip"],
                        capture_output=True,
                        text=True,
                    )
                    rows = [
                        ln.split() for ln in a.stdout.splitlines() if re.match(r"^\S+\s+\S+\s+(CVE|PYSEC|GHSA)-", ln)
                    ]
                    out += [
                        f"pip-audit {rel}: {r[0]} {r[1]} {r[2]} (fix: {r[FIX_COLUMN] if len(r) > FIX_COLUMN else '?'})"
                        for r in rows[:12]
                    ]
    return out


def main():
    ap = argparse.ArgumentParser(description="Audit a repo against house-style (read-only).")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--workspace", help="parent dir of your other projects: detect port collisions across them")
    ap.add_argument("--ignore", default="", help="comma-separated folder names to skip")
    ap.add_argument("--deep", action="store_true", help="also run ruff (security/smells) and pip-audit via uvx")
    a = ap.parse_args()
    root = Path(a.path).resolve()
    ignore = {x for x in a.ignore.split(",") if x}
    total, by_rule, files = 0, Counter(), 0
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).parts
        if p.suffix.lower() not in EXT or not p.is_file() or SKIP & set(rel) or ignore & set(rel):
            continue
        try:
            found = checks.check(p.relative_to(root), p.read_text(errors="ignore"))
        except OSError:
            continue
        if found:
            files += 1
            total += len(found)
            by_rule.update(r for _, r, _ in found)
            for n, rid, msg in found[:5]:
                print(f"{p.relative_to(root)}:{n} [{rid}] {msg}")
    print(
        f"\n{total} code violation(s) in {files} file(s): "
        + (", ".join(f"{k}={v}" for k, v in by_rule.most_common()) or "clean")
    )
    repo = hygiene.check_repo(root)
    print("docs/release hygiene: " + ("clean" if not repo else ""))
    for m in repo:
        print(f"  - {m}")
    proj = project.check_project(root, a.workspace, ignore)
    print("project standards (uv, tests, coverage, compose, ports, CDK, e2e): " + ("clean" if not proj else ""))
    for m in proj:
        print(f"  - {m}")
    tools = deep(root, ignore) if a.deep else []
    if a.deep:
        print("deep scan (ruff security/smells, pip-audit): " + ("clean" if not tools else ""))
        for m in tools:
            print(f"  - {m}")
    return 1 if total or repo or proj or tools else 0


if __name__ == "__main__":
    sys.exit(main())
