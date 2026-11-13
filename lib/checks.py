"""house-style violation detector. Shared by the PreToolUse guard and the audit script. Stdlib only.

check(path, text) -> [(line_no, rule_id, message)]. A line containing `house-style: allow` is skipped.
"""

import re
from pathlib import Path

ALLOW = "house-style: allow"
UI_EXT = {".tsx", ".jsx", ".css", ".scss", ".html", ".vue", ".svelte"}  # .mdx is prose content, not UI
MARKUP_EXT = {".tsx", ".jsx", ".html", ".vue", ".svelte"}
TOKEN_FILES = re.compile(
    r"(tokens|theme|brand|house-style|tailwind\.config|globals\.css|\.svg$|app\.config|\.test\.|\.spec\.|__tests__|e2e/)",
    re.I,
)

HEX = re.compile(r"(?<![\w&/#])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b(?!-)")
FUNC_COLOR = re.compile(r"\b(?:rgba?|hsla?)\(\s*\d")
EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿⭐⭕️]")
IMG_NO_ALT = re.compile(r"<(?:img|Image)\b(?![^>]*\balt=)[^>]*>", re.I)
BAD_LIBS = re.compile(
    r"""from\s+["'](@mui/[^"']*|@emotion/[^"']*|react-icons[^"']*|@heroicons/[^"']*|@fortawesome/[^"']*|phosphor-[^"']*|@phosphor-icons/[^"']*|@expo/vector-icons[^"']*|@tabler/icons[^"']*)["']"""
)
HIDE_SCROLL = re.compile(
    r"scrollbar-width:\s*none|-webkit-scrollbar[^{]*\{[^}]*display:\s*none|\bscrollbar-hide\b|\bno-scrollbar\b"
)
OUTLINE_OFF = re.compile(r"outline:\s*(?:none|0)\b|\boutline-none\b")
FONT_IMPORT = re.compile(r"import\s*\{([^}]*)\}\s*from\s*[\"']next/font/google[\"']")
OK_FONTS = {"Geist", "Geist_Mono"}
SDK_FASTMCP = re.compile(r"from\s+mcp\.server\.fastmcp\s+import|import\s+mcp\.server\.fastmcp")
UNITTEST = re.compile(r"^\s*import unittest(?!\.mock)\b|unittest\.TestCase|^\s*from unittest import (?!mock\b)")
PLACEHOLDER = re.compile(
    r"(?i)password|changeme|secret|example|dummy|test|local|fake|placeholder|xxxx"
)  # dev placeholders are not leaks
SECURITY = (
    (
        "cors",
        re.compile(r"allow_origins\s*=\s*\[\s*[\"']\*[\"']"),
        "CORS allow_origins=['*']: list the real origins (never with credentials).",  # house-style: allow rule text
    ),
    (
        "debug",
        re.compile(r"\b(FastAPI|Flask)\([^)]*\bdebug\s*=\s*True"),
        "debug=True must not ship; drive it from an env var that defaults to off.",
    ),
    (
        "tls",
        re.compile(r"\bverify\s*=\s*False"),
        "TLS verification disabled (verify=False).",  # house-style: allow rule text
    ),
    (
        "shell",
        re.compile(r"\bshell\s*=\s*True"),
        "shell=True invites command injection; pass an argument list.",  # house-style: allow rule text
    ),
    ("eval", re.compile(r"(?<![\w.])(eval|exec)\("), "eval/exec on dynamic input; use a parser or a dispatch table."),
    ("jwt", re.compile(r"verify_signature[\"']?\s*[:=]\s*False"), "JWT signature verification disabled."),
    (
        "deserialize",
        re.compile(r"\bpickle\.loads?\(|\byaml\.load\((?![^)]*SafeLoader)"),
        "Unsafe deserialization; use json or yaml.safe_load.",
    ),
    ("sql", re.compile(r"\.execute\(\s*f[\"']"), "SQL built with an f-string; use bound parameters."),
    (
        "secret",
        re.compile(
            r"(?i)\b\w*(secret|password|passwd|token|api_?key|private_key)\s*=\s*[\"'](?!\$\{|<)(?P<v>[^\"'\s]{8,})[\"']"
        ),
        "Hard-coded secret; read it from the environment or a secret store.",
    ),
)
HAND_OAUTH = re.compile(r"custom_route\(\s*[\"']/\.well-known/oauth")

MSG_UNITTEST = "Use pytest (plain functions + fixtures), not unittest. `unittest.mock` is fine."
MSG_FASTMCP = "Use the standalone `fastmcp` package (`from fastmcp import FastMCP`), not `mcp.server.fastmcp`. See rules/mcp-oauth.md."
MSG_OAUTH = (
    "Don't hand-roll OAuth discovery routes. Use fastmcp's RemoteAuthProvider / OAuthProxy. See rules/mcp-oauth.md."
)
MSG_COLOR = (
    "Hard-coded color. Use semantic tokens (bg-background, text-foreground, bg-primary, text-muted-foreground, "
    "border-border...). Edit tokens only in house-style.css."
)
MSG_EMOJI = (
    "Emoji/symbol used as an icon. Use a Lucide icon (lucide-react / lucide-react-native) with aria-hidden, "
    "or aria-label if it is the only content."
)
MSG_LIB = "`{}` is not allowed. Icons: Lucide only. UI: shadcn/Radix + Tailwind (no MUI/Emotion)."
MSG_SCROLL = "Don't hide scrollbars (users lose scroll affordance). Style them thin instead."
MSG_ALT = 'Image without `alt`. Add meaningful alt text, or alt="" if purely decorative.'
MSG_FOCUS = "Outline removed with no replacement. Keep a visible focus style (focus-visible:ring-2 ring-ring)."


def _is_comment(line):
    s = line.strip()
    return s.startswith(("//", "/*", "*", "{/*", "#", "<!--"))


def _python_line(n, ln, is_test):
    """Findings for one line of a Python file. Tests are only policed for the runner (fixtures hold bad samples)."""
    if is_test:
        return [(n, "unittest", MSG_UNITTEST)] if UNITTEST.search(ln) else []
    found = []
    for rid, rx, msg in SECURITY:
        m = rx.search(ln)
        if m and not _is_comment(ln) and not (rid == "secret" and PLACEHOLDER.search(m.group("v"))):
            found.append((n, rid, msg))
    if SDK_FASTMCP.search(ln):
        found.append((n, "fastmcp", MSG_FASTMCP))
    if HAND_OAUTH.search(ln):
        found.append((n, "oauth", MSG_OAUTH))
    return found


def _check_python(p, lines):
    is_test = bool(re.search(r"(^|/)(tests?/|test_)", p))
    return [f for n, ln in enumerate(lines, 1) if ALLOW not in ln for f in _python_line(n, ln, is_test)]


def _ui_line(n, ln, ext, tokenfile):
    """Findings for one line of markup/CSS."""
    found = []
    code = not _is_comment(ln)
    if code and not tokenfile and (HEX.search(ln) or FUNC_COLOR.search(ln)):
        found.append((n, "color", MSG_COLOR))
    if code and ext in MARKUP_EXT and EMOJI.search(ln):
        found.append((n, "emoji", MSG_EMOJI))
    m = BAD_LIBS.search(ln)
    if m:
        found.append((n, "lib", MSG_LIB.format(m.group(1))))
    if HIDE_SCROLL.search(ln):
        found.append((n, "scrollbar", MSG_SCROLL))
    return found


def _ui_file_rules(ext, text, lines):
    """Findings that need the whole file: images without alt, removed focus outline, wrong fonts."""
    found = []
    if ext in MARKUP_EXT:
        for m in IMG_NO_ALT.finditer(text):
            n = text.count("\n", 0, m.start()) + 1
            if ALLOW not in lines[n - 1]:
                found.append((n, "alt", MSG_ALT))
    if OUTLINE_OFF.search(text) and "focus-visible" not in text and "ring" not in text:
        n = next((i for i, ln in enumerate(lines, 1) if OUTLINE_OFF.search(ln) and ALLOW not in ln), None)
        if n:
            found.append((n, "focus", MSG_FOCUS))
    for m in FONT_IMPORT.finditer(text):
        extra = {f.strip().split(" as ")[0] for f in m.group(1).split(",") if f.strip()} - OK_FONTS
        if extra:
            found.append(
                (
                    text.count("\n", 0, m.start()) + 1,
                    "font",
                    f"Fonts must be Geist / Geist_Mono (got {', '.join(sorted(extra))}).",
                )
            )
    return found


def check(path, text):
    p = str(path).replace("\\", "/")
    ext = Path(p).suffix.lower()
    lines = text.splitlines()
    if ext == ".py":
        return _check_python(p, lines)
    if ext not in UI_EXT:
        return []
    tokenfile = bool(TOKEN_FILES.search(p))
    found = [f for n, ln in enumerate(lines, 1) if ALLOW not in ln for f in _ui_line(n, ln, ext, tokenfile)]
    return found + _ui_file_rules(ext, text, lines)


def format_violations(path, found, limit=8):
    head = f"house-style: {len(found)} violation(s) in {path}"
    body = "\n".join(f"  L{n} [{rid}] {msg}" for n, rid, msg in found[:limit])
    more = f"\n  ...and {len(found) - limit} more" if len(found) > limit else ""
    return f"{head}\n{body}{more}\nFix them, or if intentional add `house-style: allow` on that line (with a reason)."
