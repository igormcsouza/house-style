#!/usr/bin/env python3
"""PreToolUse (Edit|Write|MultiEdit): block writes that break house-style, so Claude self-corrects.
Only active inside a project that opted in with .house-style.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import cfg
import checks


def new_text(tool_input):
    if "content" in tool_input:
        return tool_input["content"]
    if "new_string" in tool_input:
        return tool_input["new_string"]
    return "\n".join(e.get("new_string", "") for e in tool_input.get("edits", []))


def main():
    try:
        data = json.load(sys.stdin)
        ti = data.get("tool_input", {})
        path = ti.get("file_path", "")
        if not path or not cfg.find(Path(path).parent):
            return 0
        found = checks.check(path, new_text(ti))
    except Exception:  # a broken guard must never block work
        return 0
    if found:
        print(checks.format_violations(path, found), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
