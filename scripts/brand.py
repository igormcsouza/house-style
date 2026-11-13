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
import tokens  # noqa: E402

LUCIDE = "https://unpkg.com/lucide-static@latest/icons/{}.svg"


def glyph(name):
    if not re.fullmatch(r"[a-z0-9-]+", name):
        sys.exit("icon must be a lucide name like 'pencil-ruler'")
    for base in (Path("node_modules/lucide-static/icons"),):
        f = base / f"{name}.svg"
        if f.is_file():
            svg = f.read_text()
            break
    else:
        try:
            svg = urllib.request.urlopen(LUCIDE.format(name), timeout=15).read().decode()
        except Exception as e:
            sys.exit(f"could not fetch lucide icon '{name}' ({e}). Check the name at https://lucide.dev/icons")
    return re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1).strip()


def tile(inner, fill, ink, size=512, pad=96, radius=112, bg=True):
    s = (size - 2 * pad) / 24
    rect = f'<rect width="{size}" height="{size}" rx="{radius}" fill="{fill}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">{rect}'
            f'<g transform="translate({pad} {pad}) scale({s:.4f})" fill="none" stroke="{ink}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{inner}</g></svg>\n')


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
    if conv:
        def png(src, dst, px):
            subprocess.run([conv, "-background", "none", "-density", "600", str(out / src), "-resize", f"{px}x{px}", str(out / dst)], check=True)
        for dst, px in (("icon-1024.png", 1024), ("icon-512.png", 512), ("icon-192.png", 192), ("apple-icon.png", 180)):
            png("icon.svg", dst, px)
        png("adaptive-foreground.svg", "adaptive-foreground.png", 1024)
        subprocess.run([conv, str(out / "icon-192.png"), "-define", "icon:auto-resize=48,32,16", str(out / "favicon.ico")], check=True)
        note = "with PNGs + favicon.ico"
    else:
        note = "SVG only (install ImageMagick for PNG/ico)"
    cfg = {"name": a.name, "accent": a.accent, "icon": a.icon, "stack": a.stack}
    Path(".house-style.json").write_text(json.dumps(cfg, indent=2) + "\n")
    print(f"brand written to {out}/ {note}; .house-style.json updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
