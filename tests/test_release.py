import json

import pytest
import release
from conftest import git, write


def make_repo(d, version="0.2.0", tag=True):
    git(d, "init", "-q", "-b", "main")
    write(
        d,
        {
            "pyproject.toml": f'[project]\nname = "x"\nversion = "{version}"\n',
            "x/__init__.py": f'__version__ = "{version}"\n',
        },
    )
    git(d, "add", "-A")
    git(d, "commit", "-qm", "feat: initial import")
    if tag:
        git(d, "tag", f"v{version}")
    return d


def commit(d, msg):
    (d / "f.txt").write_text(msg)
    git(d, "add", "-A")
    git(d, "commit", "-qm", msg)


def run(d, argv, *args):
    argv("--cwd", d, *args)
    return release.main()


def test_dry_run_changes_nothing(tmp_path, argv, capsys):
    make_repo(tmp_path)
    commit(tmp_path, "feat(api): add search (#7)")
    commit(tmp_path, "fix: null title (#8)")
    commit(tmp_path, "docs: typo")
    assert run(tmp_path, argv) == 0
    out = capsys.readouterr().out
    assert "v0.2.1" in out  # 0.x: feat + fix -> patch
    assert "- add search (#7)" in out
    assert "typo" not in out
    assert "dry run" in out
    assert 'version = "0.2.0"' in (tmp_path / "pyproject.toml").read_text()


def test_apply_breaking_bumps_minor_in_0x_and_never_tags(tmp_path, argv, capsys):
    make_repo(tmp_path)
    commit(tmp_path, "feat!: drop v1 endpoints (#9)")
    assert run(tmp_path, argv, "--apply") == 0
    assert "v0.3.0" in capsys.readouterr().out
    assert 'version = "0.3.0"' in (tmp_path / "pyproject.toml").read_text()
    assert '__version__ = "0.3.0"' in (tmp_path / "x/__init__.py").read_text()
    changelog = (tmp_path / "CHANGELOG.md").read_text()
    assert "## [0.3.0]" in changelog
    assert "### Breaking changes" in changelog
    assert git(tmp_path, "rev-parse", "--abbrev-ref", "HEAD") == "release/v0.3.0"
    assert git(tmp_path, "log", "-1", "--format=%s") == "release: v0.3.0"
    assert git(tmp_path, "tag", "--list") == "v0.2.0"


def test_1x_rules(tmp_path, argv, capsys):
    make_repo(tmp_path, "1.4.2")
    with pytest.raises(SystemExit, match="nothing to release"):
        run(tmp_path, argv)
    commit(tmp_path, "chore: bump ci")
    with pytest.raises(SystemExit, match="nothing to release"):
        run(tmp_path, argv)
    commit(tmp_path, "feat: new thing")
    run(tmp_path, argv)
    assert "v1.5.0" in capsys.readouterr().out
    commit(tmp_path, "fix: x\n\nBREAKING CHANGE: flag renamed")
    run(tmp_path, argv)
    out = capsys.readouterr().out
    assert "v2.0.0" in out
    assert "Migration: flag renamed" in out


@pytest.mark.parametrize(("kind", "expected"), [("patch", "v0.2.1"), ("minor", "v0.3.0"), ("major", "v1.0.0")])
def test_explicit_bump_kinds(tmp_path, argv, capsys, kind, expected):
    make_repo(tmp_path)
    commit(tmp_path, "fix: a")
    run(tmp_path, argv, kind)
    assert expected in capsys.readouterr().out


def test_notes_sections_and_notes_out(tmp_path, argv, capsys):
    make_repo(tmp_path)
    commit(tmp_path, "refactor(core): simplify")
    commit(tmp_path, "perf: faster")
    commit(tmp_path, "not a conventional commit")
    commit(tmp_path, "release: v0.2.0 (summary)")
    out_file = tmp_path / "notes.md"
    run(tmp_path, argv, "--notes-out", out_file)
    notes = out_file.read_text()
    assert "### Changed" in notes
    assert "- simplify" in notes
    assert "conventional" not in notes
    assert "release:" not in notes


def test_prerelease_suffix(tmp_path, argv, capsys):
    make_repo(tmp_path)
    commit(tmp_path, "fix: a")
    run(tmp_path, argv, "--pre", "rc")
    assert "v0.2.1-rc.1" in capsys.readouterr().out


def test_prerelease_apply_suggests_prerelease_flag(tmp_path, argv, capsys):
    make_repo(tmp_path)
    commit(tmp_path, "fix: a")
    run(tmp_path, argv, "--apply", "--pre", "rc")
    assert "--prerelease" in capsys.readouterr().out


def test_first_release_ships_current_version(tmp_path, argv, capsys):
    make_repo(tmp_path, "0.1.0", tag=False)
    run(tmp_path, argv)
    out = capsys.readouterr().out
    assert "v0.1.0" in out
    assert "v0.1.1" not in out


def test_first_release_without_any_version_is_0_1_0(tmp_path, argv, capsys):
    git(tmp_path, "init", "-q", "-b", "main")
    commit(tmp_path, "feat: first")
    run(tmp_path, argv)
    out = capsys.readouterr().out
    assert "v0.1.0" in out
    assert "git tag + CHANGELOG only" in out


def test_no_version_files_uses_tag(tmp_path, argv, capsys):
    git(tmp_path, "init", "-q", "-b", "main")
    commit(tmp_path, "feat: first")
    git(tmp_path, "tag", "v0.1.0")
    commit(tmp_path, "fix: second (#2)")
    assert run(tmp_path, argv, "--apply") == 0
    assert "## [0.1.1]" in (tmp_path / "CHANGELOG.md").read_text()
    assert git(tmp_path, "log", "-1", "--format=%s") == "release: v0.1.1"


def test_disagreeing_version_files_abort(tmp_path, argv):
    make_repo(tmp_path)
    (tmp_path / "x/__init__.py").write_text('__version__ = "9.9.9"\n')
    with pytest.raises(SystemExit, match="disagree"):
        run(tmp_path, argv)


def test_dirty_tree_refuses_apply(tmp_path, argv):
    make_repo(tmp_path)
    commit(tmp_path, "fix: a")
    (tmp_path / "dirty.txt").write_text("x")
    with pytest.raises(SystemExit, match="not clean"):
        run(tmp_path, argv, "--apply")


def test_apply_on_feature_branch_stays_and_extends_changelog(tmp_path, argv):
    make_repo(tmp_path)
    git(tmp_path, "switch", "-qc", "my-branch")
    write(tmp_path, {"CHANGELOG.md": "# Changelog\n\n## [0.2.0] - old\n\nstuff\n"})
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "docs: changelog")
    commit(tmp_path, "fix: a")
    run(tmp_path, argv, "--apply")
    assert git(tmp_path, "rev-parse", "--abbrev-ref", "HEAD") == "my-branch"
    text = (tmp_path / "CHANGELOG.md").read_text()
    assert text.index("## [0.2.1]") < text.index("## [0.2.0]")


def test_changelog_without_sections_gets_appended(tmp_path, argv):
    make_repo(tmp_path)
    write(tmp_path, {"CHANGELOG.md": "# Changelog\n"})
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "docs: changelog")
    commit(tmp_path, "fix: a")
    run(tmp_path, argv, "--apply")
    assert (tmp_path / "CHANGELOG.md").read_text().count("## [0.2.1]") == 1


def test_tag_drift_is_reported(tmp_path, argv, capsys):
    make_repo(tmp_path, "0.3.0", tag=False)
    git(tmp_path, "tag", "v0.1.0")
    commit(tmp_path, "fix: a")
    run(tmp_path, argv)
    assert "last tag v0.1.0 != version files 0.3.0" in capsys.readouterr().out


def test_prerelease_version_in_files_uses_base(tmp_path, argv, capsys):
    make_repo(tmp_path, "0.4.0-rc.1", tag=False)
    git(tmp_path, "tag", "v0.4.0-rc.1")
    commit(tmp_path, "fix: a")
    run(tmp_path, argv)
    assert "v0.4.1" in capsys.readouterr().out


def test_every_version_file_kind_is_bumped(tmp_path):
    write(
        tmp_path,
        {
            "package.json": json.dumps({"name": "x", "version": "1.0.0"}, indent=2),
            "app.json": json.dumps({"expo": {"name": "x", "version": "1.0.0"}}, indent=2),
            ".claude-plugin/plugin.json": json.dumps({"name": "x", "version": "1.0.0"}, indent=2),
            "src/pkg/__init__.py": "__version__ = '1.0.0'\n",
            "node_modules/dep/__init__.py": "__version__ = '9.9.9'\n",
            "docs/__init__.py": "no version here\n",
            "dev/pyproject.toml": '[project]\nversion = "5.0.0"\n[tool.uv]\npackage = false\n',
            "pyproject.toml": '[project]\nname = "x"\nversion = "1.0.0"\n[tool.uv]\npackage = false\n',
        },
    )
    found = {str(f.relative_to(tmp_path)) for f, _, _ in release.version_files(tmp_path)}
    assert found == {"package.json", "app.json", ".claude-plugin/plugin.json", "src/pkg/__init__.py"}


def test_app_json_without_expo_version_is_skipped(tmp_path):
    write(tmp_path, {"app.json": json.dumps({"expo": {"name": "x"}})})
    assert release.version_files(tmp_path) == []


def test_git_failure_exits(tmp_path):
    with pytest.raises(SystemExit, match="git log"):
        release.commits(tmp_path, None)
