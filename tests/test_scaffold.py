import json

import hygiene
import pytest
import scaffold
from conftest import ROOT, write


@pytest.fixture
def sc(argv, tmp_path, capsys):
    def run(stack, *args, dest=None):
        argv(stack, "--dest", dest or tmp_path, *args)
        assert scaffold.main() == 0
        return capsys.readouterr().out

    return run


def test_nextjs_scaffold_is_idempotent_and_never_overwrites(sc, tmp_path):
    sc("nextjs")
    for f in (
        "components/skeleton.tsx",
        "components/states.tsx",
        "app/loading.tsx",
        "app/layout.tsx",
        "tailwind.config.ts",
        "vitest.config.mts",
        "vitest.setup.ts",
        "tests/house-style.test.tsx",
    ):
        assert (tmp_path / f).is_file(), f
    assert "house-style.preset.js" in (tmp_path / "tailwind.config.ts").read_text()
    assert "./house-style.css" in (tmp_path / "app/layout.tsx").read_text()
    (tmp_path / "components/skeleton.tsx").write_text("mine")
    out = sc("nextjs")
    assert (tmp_path / "components/skeleton.tsx").read_text() == "mine"
    assert "components/skeleton.tsx" in out.split("skipped")[1]


def test_nextjs_notes_cover_installs_and_vitest_peer_conflict(sc):
    out = sc("nextjs")
    assert "npx shadcn@latest init" in out
    assert "@types/node@^22" in out


def test_existing_tailwind_config_is_left_alone(sc, tmp_path):
    write(tmp_path, {"tailwind.config.js": "module.exports = {}"})
    out = sc("nextjs")
    assert not (tmp_path / "tailwind.config.ts").exists()
    assert (tmp_path / "tailwind.config.js").read_text() == "module.exports = {}"
    assert "add `presets:" in out


@pytest.mark.parametrize(("version", "major"), [("^4.1.0", 4), ("~3.4.1", 3), ("", 3)])
def test_tw_major(tmp_path, version, major):
    write(tmp_path, {"package.json": json.dumps({"devDependencies": {"tailwindcss": version} if version else {}})})
    assert scaffold.tw_major(tmp_path) == major


def test_tw_major_survives_missing_or_broken_package_json(tmp_path):
    assert scaffold.tw_major(tmp_path) == 3
    write(tmp_path, {"package.json": "{broken"})
    assert scaffold.tw_major(tmp_path) == 3


def test_tailwind4_gets_no_config(sc, tmp_path):
    write(tmp_path, {"package.json": '{"devDependencies":{"tailwindcss":"^4.1.0"}}'})
    out = sc("nextjs")
    assert not (tmp_path / "tailwind.config.ts").exists()
    assert "Tailwind 4" in out


def test_css_dir_differs_from_app_dir(sc, tmp_path):
    sc("nextjs", "--css-dir", "styles")
    assert (tmp_path / "app/layout.tsx").is_file()
    assert not (tmp_path / "styles/layout.tsx").exists()
    assert '"../styles/house-style.css"' in (tmp_path / "app/layout.tsx").read_text()
    assert "./styles/house-style.preset.js" in (tmp_path / "tailwind.config.ts").read_text()


def test_existing_layout_gets_a_note(sc, tmp_path):
    write(tmp_path, {"app/layout.tsx": 'import "./globals.css";'})
    out = sc("nextjs")
    assert "layout.tsx exists: replace" in out
    assert (tmp_path / "app/layout.tsx").read_text() == 'import "./globals.css";'
    write(tmp_path, {"app/layout.tsx": 'import "./house-style.css";'})
    assert "layout.tsx exists" not in sc("nextjs")


def test_expo_scaffold(sc, tmp_path):
    sc("expo")
    assert "nativewind/preset" in (tmp_path / "tailwind.config.js").read_text()
    assert (tmp_path / "components/ActionButton.tsx").is_file()


def test_mkdocs_scaffold_maps_accent_and_copies_icon(sc, tmp_path):
    write(tmp_path, {".house-style.json": json.dumps({"name": "Demo", "accent": "violet"}), "brand/icon.svg": "<svg/>"})
    sc("mkdocs")
    yml = (tmp_path / "mkdocs.yml").read_text()
    assert "deep purple" in yml
    assert "Demo" in yml
    assert (tmp_path / "docs/assets/icon.svg").is_file()
    assert (tmp_path / ".github/workflows/docs.yml").is_file()


def test_mkdocs_without_icon(sc, tmp_path):
    sc("mkdocs", "--name", "Plain")
    assert not (tmp_path / "docs/assets/icon.svg").exists()


@pytest.mark.parametrize(("stack", "expected"), [("fastapi", "src/main.py"), ("fastmcp", "server.py")])
def test_python_app_templates_are_copied(sc, tmp_path, stack, expected):
    sc(stack)
    assert (tmp_path / expected).is_file()
    assert not list(tmp_path.rglob("__pycache__"))


def test_docker_scaffold_uses_the_project_block(sc, tmp_path):
    write(tmp_path, {".house-style.json": json.dumps({"ports": {"base": 17060}})})
    out = sc("docker", "--name", "demo")
    yml = (tmp_path / "docker-compose.yml").read_text()
    assert "${WEB_PORT:-17060}:3000" in yml
    assert "${API_PORT:-17061}:8000" in yml
    assert "{{" not in yml
    assert "17060-17069" in out
    assert (tmp_path / "backend/Dockerfile").is_file()
    assert (tmp_path / ".env.example").is_file()


def test_docker_scaffold_computes_a_block_avoiding_the_workspace(sc, tmp_path):
    ws = tmp_path / "ws"
    mine = ws / "demo"
    mine.mkdir(parents=True)
    sc("docker", "--workspace", ws, dest=mine)
    assert "docker-compose.yml" in {p.name for p in mine.iterdir()}


def test_e2e_scaffold_substitutes_the_web_port(sc, tmp_path):
    write(tmp_path, {".house-style.json": json.dumps({"ports": {"base": 17060}})})
    out = sc("e2e")
    assert '?? "17060"' in (tmp_path / "playwright.config.ts").read_text()
    assert "@axe-core/playwright" in out


def test_python_scaffold(sc, tmp_path):
    out = sc("python")
    assert (tmp_path / "ruff.toml").is_file()
    assert (tmp_path / "scripts/check.sh").stat().st_mode & 0o111
    assert "pyproject.fragment.toml" in out


def test_cdk_scaffold(sc, tmp_path):
    out = sc("cdk")
    assert (tmp_path / "infra/stacks/app_stack.py").is_file()
    assert (tmp_path / "infra/cdk.json").is_file()
    assert "hard stop" in out


def test_docs_fill_placeholders_and_pass_hygiene(sc, tmp_path):
    sc("docs", "--name", "Demo", "--owner", "me", "--repo", "demo", "--author", "Me")
    readme = (tmp_path / "README.md").read_text()
    assert "github.com/me/demo" in readme
    assert "<Name>" not in readme
    assert "badge/docs" not in readme
    assert "## Documentation" not in readme
    assert "brand/icon.svg" not in readme
    assert "Me" in (tmp_path / "LICENSE").read_text()
    assert (tmp_path / "CLAUDE.md").read_text().strip() == "@AGENTS.md"
    assert hygiene.check_repo(tmp_path) == []


def test_docs_keep_icon_and_docs_badge_when_available(sc, tmp_path):
    write(tmp_path, {"mkdocs.yml": "site_name: x", "brand/icon.svg": "<svg/>"})
    sc("docs", "--author", "Me")
    readme = (tmp_path / "README.md").read_text()
    assert "brand/icon.svg" in readme
    assert "badge/docs" in readme


def test_docs_leave_a_custom_claude_md_alone(sc, tmp_path):
    write(tmp_path, {"CLAUDE.md": "old stuff"})
    assert "move it into AGENTS.md" in sc("docs", "--author", "Me")
    assert (tmp_path / "CLAUDE.md").read_text() == "old stuff"
    write(tmp_path, {"CLAUDE.md": "@AGENTS.md\n"})
    assert "move it into" not in sc("docs", "--author", "Me")


def test_git_user_fallback(monkeypatch):
    class R:
        stdout = ""

    monkeypatch.setattr(scaffold.subprocess, "run", lambda *a, **k: R())
    assert scaffold.git_user() == "The Authors"


def test_templates_are_compliant_with_the_standard():
    import checks

    for f in (ROOT / "templates").rglob("*"):
        if f.is_file() and f.suffix in (".tsx", ".py") and "node_modules" not in f.parts:
            assert checks.check(f, f.read_text()) == [], f
