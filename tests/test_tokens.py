import build
import pytest
import tokens


def test_contrast_extremes():
    assert tokens.contrast((0, 0, 0), (1, 1, 1)) == pytest.approx(21, abs=0.1)


@pytest.mark.parametrize(
    ("hex_color", "prefix"),
    [
        ("#808080", "0 0%"),
        ("#ff0000", "0 100%"),
        ("#00ff00", "120 100%"),
        ("#0000ff", "240 100%"),
        ("#ff0080", "330 100%"),
        ("#f0f8ff", "208 100%"),
    ],
)
def test_hex_to_hsl(hex_color, prefix):
    assert tokens.hex_to_hsl(hex_color).startswith(prefix)


@pytest.mark.parametrize(
    "triplet", ["0 0% 50%", "10 80% 40%", "100 80% 60%", "200 50% 50%", "300 70% 30%", "70 60% 45%"]
)
def test_hsl_to_rgb_is_valid(triplet):
    assert all(0 <= c <= 1 for c in tokens._hsl_to_rgb(triplet))


def test_gray_hsl_roundtrip():
    assert tokens._hsl_to_rgb("0 0% 50%") == (0.5, 0.5, 0.5)


def test_on_color_picks_readable_ink():
    assert tokens.on_color("0 0% 0%", "0 0% 0%") == "0 0% 100%"
    assert tokens.on_color("0 0% 100%", "0 0% 0%") == "0 0% 0%"


def test_unknown_accent_exits():
    with pytest.raises(SystemExit, match="unknown accent"):
        tokens.schemes("pink")


def test_every_accent_passes_contrast():
    assert [m for a in tokens.ACCENTS for m in tokens.validate(a)] == []


def test_validator_can_fail(monkeypatch):
    monkeypatch.setitem(tokens.ACCENTS, "green", ("#86efac", "#14532d"))  # pale on white, dark on dark
    assert tokens.validate("green")


@pytest.mark.parametrize("tw", [3, 4])
def test_css_outputs(tw):
    css = tokens.css("blue", tw)
    assert "--primary:" in css
    assert "prefers-reduced-motion" in css
    assert ("@theme inline" in css) == (tw == 4)
    assert css.lstrip().splitlines()[1].startswith('@import "tailwindcss"') == (tw == 4)


def test_preset_maps_semantic_colors():
    preset = tokens.preset()
    assert "hsl(var(--primary))" in preset
    assert '"foreground": "hsl(var(--primary-foreground))"' in preset
    assert '"border": "hsl(var(--border))"' in preset


def test_build_check_ok(argv, capsys):
    argv("--check")
    assert build.main() == 0
    assert "pass contrast" in capsys.readouterr().out


def test_build_check_reports_failures(argv, capsys, monkeypatch):
    monkeypatch.setitem(tokens.ACCENTS, "green", ("#86efac", "#14532d"))
    argv("--check")
    assert build.main() == 1
    assert "green/" in capsys.readouterr().out


def test_build_writes_css_and_preset(argv, tmp_path, capsys):
    argv("--accent", "teal", "--out", tmp_path / "o")
    assert build.main() == 0
    assert (tmp_path / "o" / "house-style.css").is_file()
    assert (tmp_path / "o" / "house-style.preset.js").is_file()
    assert "wrote" in capsys.readouterr().out


def test_build_tailwind4_writes_only_css(argv, tmp_path, capsys):
    argv("--tailwind", 4, "--out", tmp_path)
    assert build.main() == 0
    assert not (tmp_path / "house-style.preset.js").exists()
    assert "preset" not in capsys.readouterr().out


def test_build_refuses_failing_accent(argv, tmp_path, monkeypatch):
    monkeypatch.setitem(tokens.ACCENTS, "green", ("#86efac", "#14532d"))
    argv("--out", tmp_path)
    with pytest.raises(SystemExit, match="contrast failure"):
        build.main()
