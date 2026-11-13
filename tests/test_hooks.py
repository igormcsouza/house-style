import json
import os

import cfg
import guard
import prompt_submit
import session_start
from conftest import ROOT, write


def optin(tmp_path, **conf):
    (tmp_path / ".house-style.json").write_text(
        json.dumps({"name": "Demo", "accent": "teal", "icon": "rocket", **conf})
    )
    return tmp_path


def test_cfg_find_and_load(tmp_path):
    assert cfg.find(tmp_path) is None
    assert cfg.load(tmp_path) is None
    optin(tmp_path)
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert cfg.find(nested) == tmp_path / ".house-style.json"
    assert cfg.load(nested)["accent"] == "teal"


def test_cfg_invalid_json_still_marks_the_project(tmp_path):
    (tmp_path / ".house-style.json").write_text("{nope")
    assert cfg.load(tmp_path) == {"_dir": str(tmp_path)}


# --- guard -------------------------------------------------------------------------------------------------------
BAD = '<div style={{color:"#fff"}}>🚀</div>'


def run_guard(stdin, payload):
    stdin(payload)
    return guard.main()


def test_guard_ignores_projects_that_did_not_opt_in(stdin, tmp_path):
    payload = {"tool_input": {"file_path": str(tmp_path / "a.tsx"), "content": BAD}}
    assert run_guard(stdin, payload) == 0


def test_guard_blocks_violations_in_opted_in_projects(stdin, tmp_path, capsys):
    optin(tmp_path)
    payload = {"tool_input": {"file_path": str(tmp_path / "src" / "a.tsx"), "content": BAD}}
    assert run_guard(stdin, payload) == 2
    err = capsys.readouterr().err
    assert "[color]" in err
    assert "[emoji]" in err


def test_guard_allows_compliant_edit(stdin, tmp_path):
    optin(tmp_path)
    payload = {
        "tool_input": {"file_path": str(tmp_path / "a.tsx"), "new_string": "<div className='text-foreground' />"}
    }
    assert run_guard(stdin, payload) == 0


def test_guard_checks_every_multiedit_chunk(stdin, tmp_path):
    optin(tmp_path)
    payload = {
        "tool_input": {
            "file_path": str(tmp_path / "b.css"),
            "edits": [{"new_string": "x"}, {"new_string": "color: #abc123"}],
        }
    }
    assert run_guard(stdin, payload) == 2


def test_guard_without_a_path_does_nothing(stdin):
    assert run_guard(stdin, {"tool_input": {}}) == 0


def test_guard_fails_open_on_garbage(stdin):
    assert run_guard(stdin, "not json") == 0


# --- session_start -----------------------------------------------------------------------------------------------
def start(stdin, capsys, payload):
    stdin(payload)
    assert session_start.main() == 0
    return capsys.readouterr().out


def test_session_start_silent_in_unrelated_dirs(stdin, capsys, tmp_path):
    assert start(stdin, capsys, {"cwd": str(tmp_path)}) == ""


def test_session_start_nudges_when_project_looks_like_a_target(stdin, capsys, tmp_path):
    write(tmp_path, {"package.json": '{"dependencies":{"next":"15"}}'})
    assert "/house-style:init" in start(stdin, capsys, {"cwd": str(tmp_path)})


def test_session_start_nudges_for_mkdocs_and_python(stdin, capsys, tmp_path):
    write(tmp_path, {"mkdocs.yml": "site_name: x"})
    assert "init" in start(stdin, capsys, {"cwd": str(tmp_path)})


def test_session_start_ignores_package_json_without_a_framework(stdin, capsys, tmp_path):
    write(tmp_path, {"package.json": '{"dependencies":{"left-pad":"1"}}'})
    assert start(stdin, capsys, {"cwd": str(tmp_path)}) == ""


def test_session_start_survives_unreadable_marker_files(stdin, capsys, tmp_path):
    f = write(tmp_path, {"package.json": '{"next":1}'}) / "package.json"
    f.chmod(0)
    try:
        assert start(stdin, capsys, {"cwd": str(tmp_path)}) == ""
    finally:
        f.chmod(0o644)


def test_session_start_injects_core_rules_and_brand(stdin, capsys, tmp_path):
    optin(tmp_path)
    out = json.loads(start(stdin, capsys, {"cwd": str(tmp_path)}))["hookSpecificOutput"]["additionalContext"]
    assert "accent=teal" in out
    assert str(ROOT) in out
    assert "{ROOT}" not in out


def test_session_start_falls_back_to_cwd_and_bad_stdin(stdin, capsys, tmp_path, monkeypatch):
    optin(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert "accent=teal" in start(stdin, capsys, "not json")


# --- prompt_submit -----------------------------------------------------------------------------------------------
def prompt(stdin, capsys, tmp_path, text):
    stdin({"cwd": str(tmp_path), "prompt": text})
    assert prompt_submit.main() == 0
    return capsys.readouterr().out


def test_prompt_routes_to_the_matching_rule_file(stdin, capsys, tmp_path):
    optin(tmp_path)
    cases = {
        "add a loading spinner to the login page": "loading.md",
        "cut a new release and bump the version": "releasing.md",
        "rewrite the README": "docs.md",
        "use uv and pytest": "python.md",
        "write the docker compose file": "infra.md",
        "add a playwright test": "testing.md",
        "is this secure against xss": "security.md",
        "improve the a11y": "a11y.md",
        "style the button color": "ui.md",
        "build an mcp server with oauth": "mcp-oauth.md",
        "add an api endpoint": "backend.md",
    }
    for text, rule in cases.items():
        assert rule in prompt(stdin, capsys, tmp_path, text), text


def test_prompt_silent_without_match_or_optin(stdin, capsys, tmp_path):
    assert prompt(stdin, capsys, tmp_path, "add a loading spinner") == ""  # not opted in
    optin(tmp_path)
    assert prompt(stdin, capsys, tmp_path, "rename a variable") == ""


def test_prompt_fails_open_on_bad_input(stdin):
    stdin("not json")
    assert prompt_submit.main() == 0


def test_hooks_json_points_at_existing_scripts():
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
    for entries in hooks.values():
        for entry in entries:
            for h in entry["hooks"]:
                script = h["command"].split("${CLAUDE_PLUGIN_ROOT}/")[1].rstrip('"')
                assert os.path.isfile(ROOT / script)
