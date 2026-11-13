import json
import stat

import brand
import pytest
from conftest import write

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M3 3a10 10 0 0010 10"/></svg>'


@pytest.mark.parametrize(
    ("raw", "fixed"),
    [
        ("M3 3a10 10 0 0010-10z", "M3 3a10 10 0 0 0 10 -10 z"),
        ("A5,5,0,01-5,5", "A5 5 0 0 1 -5 5 "),
        ("a2 2 0 1 0 4 0 2 2 0 1 0 -4 0", "a2 2 0 1 0 4 0 2 2 0 1 0 -4 0 "),
        ("a1 2", "a1 2"),
        ("M0 0L5 5", "M0 0L5 5"),
    ],
)
def test_fix_arcs(raw, fixed):
    assert brand.fix_arcs(raw) == fixed


def test_glyph_reads_a_local_lucide_install(tmp_path, monkeypatch):
    write(tmp_path, {"node_modules/lucide-static/icons/leaf.svg": SVG})
    monkeypatch.chdir(tmp_path)
    assert "a10 10 0 0 0 10 10" in brand.glyph("leaf")


def test_glyph_rejects_bad_names():
    with pytest.raises(SystemExit, match="lucide name"):
        brand.glyph("../etc/passwd")


def test_glyph_fetches_when_not_installed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    class Resp:
        def read(self):
            return SVG.encode()

    monkeypatch.setattr(brand.urllib.request, "urlopen", lambda url, timeout: Resp())
    assert "<path" in brand.glyph("leaf")


def test_glyph_fetch_failure_exits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def boom(url, timeout):
        raise OSError("offline")

    monkeypatch.setattr(brand.urllib.request, "urlopen", boom)
    with pytest.raises(SystemExit, match="could not fetch"):
        brand.glyph("leaf")


def test_tile_with_and_without_background():
    assert "<rect" in brand.tile("<path/>", "#15803d", "#ffffff")
    assert "<rect" not in brand.tile("<path/>", "#15803d", "#ffffff", bg=False)


def test_rgb_converts_hsl_triplets():
    assert brand.rgb("0 0% 100%") == "#ffffff"


def fake_tools(tmp_path, monkeypatch, convert=True, rsvg=False):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    if convert:  # last argument is the output file
        (bin_dir / "convert").write_text('#!/bin/sh\nfor a; do last="$a"; done\n: > "$last"\n')
    if rsvg:  # output follows -o
        (bin_dir / "rsvg-convert").write_text(
            '#!/bin/sh\nwhile [ $# -gt 0 ]; do [ "$1" = "-o" ] && out="$2"; shift; done\n: > "$out"\n'
        )
    for f in bin_dir.iterdir():
        f.chmod(f.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", str(bin_dir))


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    work = tmp_path / "work"
    write(work, {"node_modules/lucide-static/icons/leaf.svg": SVG})
    monkeypatch.chdir(work)
    return work


def test_main_generates_svg_png_ico_and_config(project_dir, argv, capsys, monkeypatch):
    fake_tools(project_dir.parent, monkeypatch)
    argv("--name", "Demo", "--icon", "leaf", "--accent", "violet", "--stack", "nextjs")
    assert brand.main() == 0
    for f in (
        "icon.svg",
        "adaptive-foreground.svg",
        "adaptive-background.txt",
        "icon-1024.png",
        "apple-icon.png",
        "favicon.ico",
        "adaptive-foreground.png",
    ):
        assert (project_dir / "brand" / f).exists(), f
    assert "with PNGs" in capsys.readouterr().out
    cfg = json.loads((project_dir / ".house-style.json").read_text())
    assert cfg["accent"] == "violet"
    assert cfg["stack"] == "nextjs"


def test_main_prefers_rsvg_convert_when_installed(project_dir, argv, monkeypatch):
    fake_tools(project_dir.parent, monkeypatch, rsvg=True)
    argv("--name", "Demo", "--icon", "leaf")
    brand.main()
    assert (project_dir / "brand" / "icon-512.png").exists()


def test_main_without_imagemagick_still_writes_svg(project_dir, argv, capsys, monkeypatch):
    fake_tools(project_dir.parent, monkeypatch, convert=False)
    argv("--name", "Demo", "--icon", "leaf")
    brand.main()
    assert "SVG only" in capsys.readouterr().out
    assert (project_dir / "brand" / "icon.svg").exists()
    assert not (project_dir / "brand" / "icon-512.png").exists()


def test_main_keeps_existing_config_keys(project_dir, argv, monkeypatch):
    fake_tools(project_dir.parent, monkeypatch, convert=False)
    write(project_dir, {".house-style.json": json.dumps({"ports": {"base": 17060}, "ignore": ["x"]})})
    argv("--name", "Demo", "--icon", "leaf")
    brand.main()
    cfg = json.loads((project_dir / ".house-style.json").read_text())
    assert cfg["ports"] == {"base": 17060}
    assert cfg["ignore"] == ["x"]
    assert cfg["name"] == "Demo"
