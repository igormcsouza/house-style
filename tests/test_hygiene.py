import json

import hygiene
from conftest import ROOT, git, write


def good_repo(tmp_path):
    for src in ("README.md", "AGENTS.md"):
        write(tmp_path, {src: (ROOT / "templates" / src).read_text()})
    write(tmp_path, {"LICENSE": "MIT", "CLAUDE.md": "@AGENTS.md\n"})
    return tmp_path


def msgs(path):
    return " | ".join(hygiene.check_repo(path))


def test_empty_repo_lists_missing_files(tmp_path):
    m = msgs(tmp_path)
    for k in ("README.md missing", "AGENTS.md missing", "LICENSE missing"):
        assert k in m


def test_templates_are_clean(tmp_path):
    assert hygiene.check_repo(good_repo(tmp_path)) == []


def test_readme_problems(tmp_path):
    write(good_repo(tmp_path), {"README.md": "no title\n## Usage\n"})
    assert "no H1" in msgs(tmp_path)
    assert "no Install" in msgs(tmp_path)
    write(tmp_path, {"README.md": "# T\n## Install 🚀\n" + "x\n" * 300})
    m = msgs(tmp_path)
    assert "headings contain emoji" in m
    assert "300" in m or "302" in m


def test_agents_too_long_and_claude_md_content(tmp_path):
    write(good_repo(tmp_path), {"AGENTS.md": "x\n" * 250, "CLAUDE.md": "lots of stuff"})
    m = msgs(tmp_path)
    assert "AGENTS.md > 200" in m
    assert "CLAUDE.md should contain only" in m


def test_tags_and_changelog(tmp_path):
    good_repo(tmp_path)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "feat: x")
    git(tmp_path, "tag", "0.1.0")
    m = msgs(tmp_path)
    assert "not in vX.Y.Z form" in m
    assert "CHANGELOG.md missing" in m
    git(tmp_path, "tag", "-d", "0.1.0")
    git(tmp_path, "tag", "v0.1.0")
    write(tmp_path, {"CHANGELOG.md": "# Changelog\n"})
    assert hygiene.check_repo(tmp_path) == []


def test_pinned_plugin_version_is_flagged(tmp_path):
    good_repo(tmp_path)
    write(tmp_path, {".claude-plugin/plugin.json": json.dumps({"name": "x", "version": "1.0.0"})})
    assert "pins `version`" in msgs(tmp_path)
    write(tmp_path, {".claude-plugin/plugin.json": json.dumps({"name": "x"})})
    assert "pins `version`" not in msgs(tmp_path)
    write(tmp_path, {".claude-plugin/plugin.json": "{broken"})
    assert "not valid JSON" in msgs(tmp_path)
