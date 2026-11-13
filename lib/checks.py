"""house-style violation detector. Shared by the PreToolUse guard and the audit script. Stdlib only.

check(path, text) -> [(line_no, rule_id, message)]. A line containing `house-style: allow` is skipped.
"""
import re
from pathlib import Path

ALLOW = "house-style: allow"
UI_EXT = {".tsx", ".jsx", ".css", ".scss", ".html", ".vue", ".svelte"}  # .mdx is prose content, not UI
MARKUP_EXT = {".tsx", ".jsx", ".html", ".vue", ".svelte"}
TOKEN_FILES = re.compile(r"(tokens|theme|brand|house-style|tailwind\.config|globals\.css|\.svg$|app\.config|\.test\.|\.spec\.|__tests__|e2e/)", re.I)

HEX = re.compile(r"(?<![\w&/#])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b(?!-)")
FUNC_COLOR = re.compile(r"\b(?:rgba?|hsla?)\(\s*\d")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⭕️]")
IMG_NO_ALT = re.compile(r"<(?:img|Image)\b(?![^>]*\balt=)[^>]*>", re.I)
BAD_LIBS = re.compile(r"""from\s+["'](@mui/[^"']*|@emotion/[^"']*|react-icons[^"']*|@heroicons/[^"']*|@fortawesome/[^"']*|phosphor-[^"']*|@phosphor-icons/[^"']*|@expo/vector-icons[^"']*|@tabler/icons[^"']*)["']""")
HIDE_SCROLL = re.compile(r"scrollbar-width:\s*none|-webkit-scrollbar[^{]*\{[^}]*display:\s*none|\bscrollbar-hide\b|\bno-scrollbar\b")
OUTLINE_OFF = re.compile(r"outline:\s*(?:none|0)\b|\boutline-none\b")
FONT_IMPORT = re.compile(r"import\s*\{([^}]*)\}\s*from\s*[\"']next/font/google[\"']")
OK_FONTS = {"Geist", "Geist_Mono"}
SDK_FASTMCP = re.compile(r"from\s+mcp\.server\.fastmcp\s+import|import\s+mcp\.server\.fastmcp")
HAND_OAUTH = re.compile(r"custom_route\(\s*[\"']/\.well-known/oauth")


def _is_comment(line):
    s = line.strip()
    return s.startswith(("//", "/*", "*", "{/*", "#", "<!--"))


def check(path, text):
    p = str(path).replace("\\", "/")
    ext = Path(p).suffix.lower()
    out = []
    lines = text.splitlines()
    if ext == ".py":
        if re.search(r"(^|/)(tests?/|test_)", p):
            return out  # fixtures legitimately contain violating samples
        for n, ln in enumerate(lines, 1):
            if ALLOW in ln:
                continue
            if SDK_FASTMCP.search(ln):
                out.append((n, "fastmcp", "Use the standalone `fastmcp` package (`from fastmcp import FastMCP`), not `mcp.server.fastmcp`. See rules/mcp-oauth.md."))
            if HAND_OAUTH.search(ln):
                out.append((n, "oauth", "Don't hand-roll OAuth discovery routes. Use fastmcp's RemoteAuthProvider / OAuthProxy. See rules/mcp-oauth.md."))
        return out
    if ext not in UI_EXT:
        return out
    tokenfile = bool(TOKEN_FILES.search(p))
    for n, ln in enumerate(lines, 1):
        if ALLOW in ln:
            continue
        code = not _is_comment(ln)
        if code and not tokenfile and (HEX.search(ln) or FUNC_COLOR.search(ln)):
            out.append((n, "color", "Hard-coded color. Use semantic tokens (bg-background, text-foreground, bg-primary, text-muted-foreground, border-border...). Edit tokens only in house-style.css."))
        if code and ext in MARKUP_EXT and EMOJI.search(ln):
            out.append((n, "emoji", "Emoji/symbol used as an icon. Use a Lucide icon (lucide-react / lucide-react-native) with aria-hidden, or aria-label if it is the only content."))
        m = BAD_LIBS.search(ln)
        if m:
            out.append((n, "lib", f"`{m.group(1)}` is not allowed. Icons: Lucide only. UI: shadcn/Radix + Tailwind (no MUI/Emotion)."))
        if HIDE_SCROLL.search(ln):
            out.append((n, "scrollbar", "Don't hide scrollbars (users lose scroll affordance). Style them thin instead."))
    if ext in MARKUP_EXT:
        for m in IMG_NO_ALT.finditer(text):
            n = text.count("\n", 0, m.start()) + 1
            if ALLOW not in lines[n - 1]:
                out.append((n, "alt", 'Image without `alt`. Add meaningful alt text, or alt="" if purely decorative.'))
    if OUTLINE_OFF.search(text) and "focus-visible" not in text and "ring" not in text:
        n = next((i for i, ln in enumerate(lines, 1) if OUTLINE_OFF.search(ln) and ALLOW not in ln), None)
        if n:
            out.append((n, "focus", "Outline removed with no replacement. Keep a visible focus style (focus-visible:ring-2 ring-ring)."))
    for m in FONT_IMPORT.finditer(text):
        extra = {f.strip().split(" as ")[0] for f in m.group(1).split(",") if f.strip()} - OK_FONTS
        if extra:
            out.append((text.count("\n", 0, m.start()) + 1, "font", f"Fonts must be Geist / Geist_Mono (got {', '.join(sorted(extra))})."))
    return out


def format_violations(path, found, limit=8):
    head = f"house-style: {len(found)} violation(s) in {path}"
    body = "\n".join(f"  L{n} [{rid}] {msg}" for n, rid, msg in found[:limit])
    more = f"\n  ...and {len(found) - limit} more" if len(found) > limit else ""
    return f"{head}\n{body}{more}\nFix them, or if intentional add `house-style: allow` on that line (with a reason)."
