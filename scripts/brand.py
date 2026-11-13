#!/usr/bin/env python3
"""Generate a project's icon set from a Lucide glyph on an accent tile, and write .house-style.json.
  brand.py --name Draftr --icon pencil-ruler --accent green [--out brand] [--stack nextjs|expo|mkdocs|api]
Outputs in --out: icon.svg, icon-1024.png, icon-512.png, icon-192.png, apple-icon.png, favicon.ico,
adaptive-foreground.png (+ adaptive-background.txt). PNGs need ImageMagick (`convert`); SVG always works."""

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import tokens

LUCIDE = "https://unpkg.com/lucide-static@latest/icons/{}.svg"


NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
SEP = " ,\t\n\r"
ARC_PARAMS = 7  # rx ry rotation large-arc-flag sweep-flag x y
FLAG_POSITIONS = (3, 4)
TILE, RADIUS = 512, 112


def glyph(name):
    if not re.fullmatch(r"[a-z0-9-]+", name):
        sys.exit("icon must be a lucide name like 'pencil-ruler'")
    local = Path("node_modules/lucide-static/icons") / f"{name}.svg"
    if local.is_file():
        svg = local.read_text()
    else:
        try:
            svg = urllib.request.urlopen(LUCIDE.format(name), timeout=15).read().decode()
        except OSError as e:
            sys.exit(f"could not fetch lucide icon '{name}' ({e}). Check the name at https://lucide.dev/icons")
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1).strip()
    return re.sub(r'(\sd=")([^"]*)(")', lambda m: m.group(1) + fix_arcs(m.group(2)) + m.group(3), inner)


def _skip(d, i):
    while i < len(d) and d[i] in SEP:
        i += 1
    return i


def _arc_params(d, i):
    """Read up to 7 arc parameters starting at i; the two flags are single characters that may touch the next number."""
    vals = []
    for k in range(ARC_PARAMS):
        i = _skip(d, i)
        if k in FLAG_POSITIONS and i < len(d) and d[i] in "01":
            vals.append(d[i])
            i += 1
            continue
        m = NUM.match(d, i)
        if not m:
            break
        vals.append(m.group())
        i = m.end()
    return vals, i


def fix_arcs(d):
    """Expand SVG path arc commands so every flag is its own token (`a10 10 0 0010-10` -> `a10 10 0 0 0 10 -10`).
    ImageMagick's built-in renderer cannot parse the compact form that Lucide uses."""
    out, i = [], 0
    while i < len(d):
        c = d[i]
        out.append(c)
        i += 1
        if c not in "aA":
            continue
        while True:
            vals, i = _arc_params(d, i)
            if len(vals) < ARC_PARAMS:
                out.append(" ".join(vals))
                break
            out.append(" ".join(vals) + " ")
            j = _skip(d, i)
            if j < len(d) and d[j] in "-+.0123456789":  # implicit repeated arc
                i = j
                continue
            break
    return "".join(out)


def tile(inner, fill, ink, pad=96, bg=True):
    s = (TILE - 2 * pad) / 24
    rect = f'<rect width="{TILE}" height="{TILE}" rx="{RADIUS}" fill="{fill}"/>' if bg else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TILE} {TILE}" width="{TILE}" height="{TILE}">{rect}'
        f'<g transform="translate({pad} {pad}) scale({s:.4f})" fill="none" stroke="{ink}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{inner}</g></svg>\n'
    )


def rgb(triplet):
    return "#" + "".join(f"{round(c * 255):02x}" for c in tokens._hsl_to_rgb(triplet))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--name", required=True)
    a.add_argument("--icon", required=True)
    a.add_argument("--accent", default=tokens.DEFAULT_ACCENT)
    a.add_argument("--out", default="brand")
    a.add_argument("--stack", default="")
    a = a.parse_args()
    light, _ = tokens.schemes(a.accent)
    fill = tokens.ACCENTS[a.accent][0]
    ink = rgb(light["primary-foreground"])
    inner = glyph(a.icon)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "icon.svg").write_text(tile(inner, fill, ink))
    (out / "adaptive-foreground.svg").write_text(tile(inner, fill, ink, pad=170, bg=False))
    (out / "adaptive-background.txt").write_text(fill + "\n")
    conv = shutil.which("magick") or shutil.which("convert")
    rsvg = shutil.which("rsvg-convert")
    if conv:

        def png(src, dst, px):
            if rsvg:  # best fidelity when installed (apt install librsvg2-bin)
                subprocess.run([rsvg, "-w", str(px), "-h", str(px), "-o", str(out / dst), str(out / src)], check=True)
            else:
                subprocess.run(
                    [
                        conv,
                        "-background",
                        "none",
                        "-density",
                        "600",
                        str(out / src),
                        "-resize",
                        f"{px}x{px}",
                        str(out / dst),
                    ],
                    check=True,
                )

        for dst, px in (("icon-1024.png", 1024), ("icon-512.png", 512), ("icon-192.png", 192), ("apple-icon.png", 180)):
            png("icon.svg", dst, px)
        png("adaptive-foreground.svg", "adaptive-foreground.png", 1024)
        subprocess.run(
            [conv, str(out / "icon-192.png"), "-define", "icon:auto-resize=48,32,16", str(out / "favicon.ico")],
            check=True,
        )
        note = "with PNGs + favicon.ico"
    else:
        note = "SVG only (install ImageMagick for PNG/ico)"
    f = Path(".house-style.json")
    cfg = json.loads(f.read_text()) if f.is_file() else {}
    cfg.update({"name": a.name, "accent": a.accent, "icon": a.icon, "stack": a.stack})  # keep ports and any other keys
    f.write_text(json.dumps(cfg, indent=2) + "\n")
    print(f"brand written to {out}/ {note}; .house-style.json updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
