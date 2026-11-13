import subprocess

import audit
from conftest import ROOT, write


def good(tmp_path):
    for src in ("README.md", "AGENTS.md"):
        write(tmp_path, {src: (ROOT / "templates" / src).read_text()})
    write(tmp_path, {"LICENSE": "MIT", "CLAUDE.md": "@AGENTS.md\n"})
    return tmp_path


def run(argv, capsys, path, *args):
    argv(path, *args)
    code = audit.main()
    return code, capsys.readouterr().out


def test_clean_repo_exits_zero(tmp_path, argv, capsys):
    code, out = run(argv, capsys, good(tmp_path))
    assert code == 0
    assert "0 code violation(s) in 0 file(s): clean" in out
    assert "docs/release hygiene: clean" in out
    assert "project standards" in out


def test_reports_code_violations_with_counts(tmp_path, argv, capsys):
    write(
        good(tmp_path),
        {
            "src/a.tsx": '<div style={{color: "#fff"}}>🚀</div>',
            "node_modules/x/a.tsx": "#fff 🚀",
            "legacy/b.tsx": "<p style={{color:'#000'}}/>",
        },
    )
    code, out = run(argv, capsys, tmp_path)
    assert code == 1
    assert "src/a.tsx:1 [color]" in out
    assert "color=2" not in out or "legacy" in out
    assert "node_modules" not in out
    code, out = run(argv, capsys, tmp_path, "--ignore", "legacy")
    assert "legacy" not in out


def test_unreadable_files_are_skipped(tmp_path, argv, capsys):
    f = write(good(tmp_path), {"a.tsx": "#fff"}) / "a.tsx"
    f.chmod(0)
    try:
        code, out = run(argv, capsys, tmp_path)
    finally:
        f.chmod(0o644)
    assert code == 0
    assert "a.tsx" not in out


def test_hygiene_and_project_findings_fail_the_audit(tmp_path, argv, capsys):
    write(tmp_path, {"backend/pyproject.toml": '[project]\nname="x"\ndependencies=["fastapi"]\n'})
    code, out = run(argv, capsys, tmp_path)
    assert code == 1
    assert "README.md missing" in out
    assert "uv.lock missing" in out


def test_workspace_flag_reports_collisions(tmp_path, argv, capsys):
    ws = tmp_path / "ws"
    write(
        ws, {"a/docker-compose.yml": '    ports: ["12000:80"]\n', "b/docker-compose.yml": '    ports: ["12000:80"]\n'}
    )
    _code, out = run(argv, capsys, ws / "a", "--workspace", ws)
    assert "also claimed by project 'b'" in out


# --- --deep ------------------------------------------------------------------------------------------------------
def cp(stdout="", returncode=0):
    return subprocess.CompletedProcess([], returncode, stdout, "")


def test_deep_needs_uv(monkeypatch, tmp_path):
    monkeypatch.setattr(audit.shutil, "which", lambda _: None)
    assert "needs uv" in audit.deep(tmp_path, set())[0]


def test_deep_summarizes_ruff_and_lists_security_and_cves(monkeypatch, tmp_path):
    write(tmp_path, {"api/pyproject.toml": "[project]\n", "api/uv.lock": "", "docs/readme.md": ""})
    monkeypatch.setattr(audit.shutil, "which", lambda _: "/usr/bin/uv")

    def fake(cmd, **kw):
        joined = " ".join(map(str, cmd))
        if "ruff" in joined:
            return cp(
                f"{tmp_path}/api/a.py:1:1: S105 Possible hardcoded password\n{tmp_path}/api/a.py:2:1: PLR2004 magic\n"
                f"{tmp_path}/api/a.py:3:1: PLR2004 magic\nnoise line\n"
            )
        if "export" in joined:
            return cp()
        return cp("Name Version ID Fix\nurllib3 2.7.0 PYSEC-1 2.8.0\nwerkzeug 3.1.8 CVE-2 3.1.9\nhttpx 1.0 GHSA-3\n")

    monkeypatch.setattr(audit.subprocess, "run", fake)
    out = audit.deep(tmp_path, set())
    assert any("S105" in m and "api/a.py:1:1" in m for m in out)
    assert any("PLR2004 x2" in m for m in out)
    assert "pip-audit api: urllib3 2.7.0 PYSEC-1 (fix: 2.8.0)" in out
    assert any("httpx 1.0 GHSA-3 (fix: ?)" in m for m in out)


def test_deep_skips_audit_when_export_fails_and_when_ruff_is_clean(monkeypatch, tmp_path):
    write(tmp_path, {"api/pyproject.toml": "[project]\n", "api/uv.lock": "", "noproj/readme.md": ""})
    monkeypatch.setattr(audit.shutil, "which", lambda _: "/usr/bin/uv")
    monkeypatch.setattr(audit.subprocess, "run", lambda cmd, **kw: cp(returncode=1) if "export" in cmd else cp())
    assert audit.deep(tmp_path, set()) == []


def test_main_with_deep_prints_the_section(tmp_path, argv, capsys, monkeypatch):
    monkeypatch.setattr(audit, "deep", lambda root, ignore: ["ruff something"])
    code, out = run(argv, capsys, good(tmp_path), "--deep")
    assert code == 1
    assert "deep scan" in out
    assert "ruff something" in out
    monkeypatch.setattr(audit, "deep", lambda root, ignore: [])
    code, out = run(argv, capsys, tmp_path, "--deep")
    assert code == 0
    assert "deep scan (ruff security/smells, pip-audit): clean" in out
