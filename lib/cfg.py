"""Find and read a project's .house-style.json (opt-in marker). Stdlib only."""
import json
from pathlib import Path

NAME = ".house-style.json"
ROOT = Path(__file__).resolve().parent.parent


def find(start):
    p = Path(start).resolve()
    for d in [p, *p.parents]:
        f = d / NAME
        if f.is_file():
            return f
    return None


def load(start):
    f = find(start)
    if not f:
        return None
    try:
        return {**json.loads(f.read_text()), "_dir": str(f.parent)}
    except (OSError, ValueError):
        return {"_dir": str(f.parent)}
