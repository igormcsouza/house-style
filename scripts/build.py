#!/usr/bin/env python3
"""Emit house-style tokens for a project.
  build.py --accent green --out DIR [--tailwind 3|4]   -> DIR/house-style.css (+ house-style.preset.js for tailwind 3)
  build.py --check                                      -> validate contrast of every accent (exit 1 on failure)"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import tokens  # noqa: E402


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--accent", default=tokens.DEFAULT_ACCENT)
    a.add_argument("--out", default=".")
    a.add_argument("--tailwind", type=int, choices=(3, 4), default=3)
    a.add_argument("--check", action="store_true")
    a = a.parse_args()
    if a.check:
        bad = [m for n in tokens.ACCENTS for m in tokens.validate(n)]
        print("\n".join(bad) or f"all {len(tokens.ACCENTS)} accents pass contrast")
        return 1 if bad else 0
    bad = tokens.validate(a.accent)
    if bad:
        sys.exit("contrast failure:\n" + "\n".join(bad))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "house-style.css").write_text(tokens.css(a.accent, a.tailwind))
    if a.tailwind == 3:
        (out / "house-style.preset.js").write_text(tokens.preset())
    print(f"wrote {out}/house-style.css" + (f" and house-style.preset.js" if a.tailwind == 3 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
