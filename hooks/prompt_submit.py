#!/usr/bin/env python3
"""UserPromptSubmit: when a prompt touches UI/backend/MCP/docs, remind Claude which rule file to read first."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import cfg

TOPICS = (
    (
        r"\b(ui|ux|page|screen|component|button|form|modal|layout|css|tailwind|style|theme|colou?r|dark mode|icon|favicon|logo|landing|dashboard|design)\b",
        "ui.md",
    ),
    (r"\b(loading|spinner|skeleton|empty state|error state|toast)\b", "loading.md"),
    (r"\b(a11y|accessib\w*|aria|contrast|keyboard|focus|screen reader)\b", "a11y.md"),
    (r"\b(mcp|oauth|auth|login|token|jwt|fastmcp)\b", "mcp-oauth.md"),
    (r"\b(api|endpoint|backend|fastapi|lambda|dynamodb|service|route)\b", "backend.md"),
    (
        r"\b(mkdocs|docs site|documentation|readme|agents\.md|claude\.md|contributing|docstring|document\w*)\b",
        "docs.md",
    ),
    (r"\b(python|uv|pytest|coverage|ruff|lint|refactor|smell\w*|clean ?code)\b", "python.md"),
    (r"\b(docker|compose|dockerfile|container|ports?|cdk|aws|infra\w*|deploy\w*|terraform|lambda)\b", "infra.md"),
    (r"\b(tests?|testing|vitest|jest|playwright|e2e|end.to.end|coverage|axe|mobile|responsive)\b", "testing.md"),
    (
        r"\b(security|secure|vulnerab\w*|cors|secrets?|xss|csrf|injection|sanitiz\w*|encrypt\w*|permissions?)\b",
        "security.md",
    ),
    (
        r"\b(release|version|versioning|tag|changelog|semver|publish|ship|bump|deliver\w*|pypi|npm publish)\b",
        "releasing.md",
    ),
)


def main():
    try:
        data = json.load(sys.stdin)
        conf = cfg.load(data.get("cwd", "."))
        if not conf:
            return 0
        prompt = data.get("prompt", "").lower()
        files = [f for rx, f in TOPICS if re.search(rx, prompt)]
    except Exception:
        return 0
    if not files:
        return 0
    paths = ", ".join(f"{cfg.ROOT}/rules/{f}" for f in dict.fromkeys(files))
    msg = f"house-style is active: before deciding anything visual, structural or auth-related, read {paths} and follow it. Steer any conflicting choice back to the standard."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
