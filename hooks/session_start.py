#!/usr/bin/env python3
"""SessionStart: inject the house-style core rules + this project's brand, or nudge to init."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import cfg  # noqa: E402

LOOKS_LIKE = (("package.json", ("\"next\"", "\"expo\"", "\"react\"")), ("mkdocs.yml", ("",)),
              ("pyproject.toml", ("fastapi", "fastmcp")), ("requirements.txt", ("fastapi", "fastmcp")))


def looks_like_target(d):
    for name, needles in LOOKS_LIKE:
        f = Path(d) / name
        if f.is_file():
            try:
                t = f.read_text(errors="ignore")
            except OSError:
                continue
            if any(n in t for n in needles):
                return True
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    cwd = data.get("cwd") or os.getcwd()
    root = str(cfg.ROOT)
    conf = cfg.load(cwd)
    if conf:
        core = (cfg.ROOT / "rules" / "core.md").read_text().replace("{ROOT}", root)
        ctx = (f"{core}\n\nThis project: name={conf.get('name', '?')}, accent={conf.get('accent', 'green')}, "
               f"icon=lucide:{conf.get('icon', '?')} (brand files in brand/). Config: {conf['_dir']}/{cfg.NAME}")
    elif looks_like_target(cwd):
        ctx = ("house-style plugin is installed but this project has no .house-style.json. If the user wants "
               "the standard UI/backend/MCP style applied, suggest running /house-style:init. Otherwise ignore.")
    else:
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
