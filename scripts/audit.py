#!/usr/bin/env python3
"""Audit a repo against house-style. Read-only. Usage: audit.py [path] ; exit 1 if violations."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import checks  # noqa: E402
import hygiene  # noqa: E402

SKIP = {"node_modules", ".next", "out", ".git", "cdk.out", "dist", "build", ".venv", "venv", "worktrees", "__pycache__", "coverage", "playwright-report", "test-results", ".expo", "android", "ios", "site"}
EXT = checks.UI_EXT | {".py"}


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    total, by_rule, files = 0, Counter(), 0
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() not in EXT or not p.is_file() or SKIP & set(p.relative_to(root).parts):
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
    print(f"\n{total} code violation(s) in {files} file(s): " + (", ".join(f"{k}={v}" for k, v in by_rule.most_common()) or "clean"))
    repo = hygiene.check_repo(root)
    print("docs/release hygiene: " + ("clean" if not repo else ""))
    for m in repo:
        print(f"  - {m}")
    return 1 if total or repo else 0


if __name__ == "__main__":
    sys.exit(main())
