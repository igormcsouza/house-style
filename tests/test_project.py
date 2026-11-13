import json

import project
import pytest
from conftest import write

PY = '[project]\nname = "x"\ndependencies = ["fastapi"]\n[tool.pytest.ini_options]\naddopts = "--cov=src --cov-fail-under=100"\n'
CDK_PY = '[project]\nname = "infra"\ndependencies = ["aws-cdk-lib"]\n[tool.pytest.ini_options]\naddopts = "--cov-fail-under=100"\n'
VITEST = "export default { test: { coverage: { thresholds: { 100: true } } } }"
NEXT = json.dumps(
    {"dependencies": {"next": "15"}, "devDependencies": {"@axe-core/playwright": "4", "eslint-config-next": "15"}}
)
COMPOSE = 'services:\n  web:\n    ports: ["12000:3000"]\n'


def full_stack():
    return {
        "backend/pyproject.toml": PY,
        "backend/uv.lock": "",
        "backend/tests/test_x.py": "",
        "web/package.json": NEXT,
        "web/vitest.config.mts": VITEST,
        "infra/pyproject.toml": CDK_PY,
        "infra/uv.lock": "",
        "infra/tests/test_x.py": "",
        "infra/cdk.json": "{}",
        "docker-compose.yml": COMPOSE,
        "playwright.config.ts": "projects: [{ use: { ...devices['Pixel 7'] } }]",
    }


def findings(tmp_path, files, **kw):
    write(tmp_path, files)
    return " | ".join(project.check_project(tmp_path, **kw))


def test_complete_project_is_clean(tmp_path):
    assert findings(tmp_path, full_stack()) == ""


def test_python_requires_uv_lock_and_rejects_other_tools(tmp_path):
    m = findings(tmp_path, {"api/pyproject.toml": PY, "api/requirements.txt": "x", "api/tests/t.py": ""})
    assert "uv.lock missing" in m
    assert "not uv (requirements.txt)" in m
    m = findings(
        tmp_path / "p", {"api/pyproject.toml": PY + "[tool.poetry]\n", "api/uv.lock": "", "api/tests/t.py": ""}
    )
    assert "[tool.poetry]" in m


def test_python_without_pyproject(tmp_path):
    assert "Python without pyproject.toml/uv" in findings(tmp_path, {"old/requirements.txt": "x", "old/app.py": ""})


def test_python_tests_and_coverage_gate(tmp_path):
    assert "no tests" in findings(tmp_path, {"a/pyproject.toml": '[project]\nname="x"\n', "a/uv.lock": ""})
    m = findings(
        tmp_path / "b",
        {
            "a/pyproject.toml": '[project]\nname="x"\n[tool.pytest.ini_options]\naddopts="--cov-fail-under=90"\n',
            "a/uv.lock": "",
        },
    )
    assert "coverage gate missing or below 100" in m
    ok = findings(
        tmp_path / "c",
        {
            "a/pyproject.toml": '[project]\nname="x"\n',
            "a/uv.lock": "",
            "a/tests/t.py": "",
            "a/.coveragerc": "[report]\nfail_under = 100\n",
        },
    )
    assert "coverage" not in ok


def test_fastapi_global_layer_folders(tmp_path):
    m = findings(tmp_path, {**full_stack(), "backend/src/services/x.py": "", "backend/app/models/y.py": ""})
    assert "backend/src/services/: global layer folder" in m
    assert "backend/app/models/" in m


def test_frontend_runner_and_thresholds(tmp_path):
    base = {
        "w/package.json": json.dumps(
            {"dependencies": {"react": "19", "next": "15"}, "devDependencies": {"eslint-config-next": "15"}}
        )
    }
    assert "no unit-test runner" in findings(tmp_path, base)
    m = findings(
        tmp_path / "a",
        {**base, "w/vitest.config.mts": "export default { test: { coverage: { thresholds: { lines: 80 } } } }"},
    )
    assert "thresholds missing or below 100" in m
    m = findings(tmp_path / "b", {**base, "w/vitest.config.mts": "export default { test: {} }"})
    assert "thresholds missing or below 100" in m
    ok = findings(tmp_path / "c", {**base, "w/vitest.config.mts": "thresholds: { lines: 100, branches: 100 }"})
    assert "thresholds" not in ok


def test_jest_coverage_threshold_in_package_json(tmp_path):
    pkg = {"dependencies": {"expo": "57"}, "jest": {"coverageThreshold": {"global": {"lines": 100}}}}
    assert "unit-test" not in findings(tmp_path, {"app/package.json": json.dumps(pkg)})


def test_next_needs_jsx_a11y_lint(tmp_path):
    m = findings(
        tmp_path, {"w/package.json": json.dumps({"dependencies": {"next": "15"}}), "w/vitest.config.mts": VITEST}
    )
    assert "no jsx-a11y lint" in m


def test_compose_required_for_apps(tmp_path):
    files = {k: v for k, v in full_stack().items() if k != "docker-compose.yml"}
    assert "no docker-compose.yml" in findings(tmp_path, files)


def test_default_and_out_of_range_ports(tmp_path):
    m = findings(
        tmp_path,
        {**full_stack(), "docker-compose.yml": 'services:\n  a:\n    ports: ["8000:8000", "58000:80", "12001:80"]\n'},
    )
    assert "default host ports [8000]" in m
    assert "outside 10000-32759" in m


def test_ports_must_stay_inside_the_configured_block(tmp_path):
    write(tmp_path, {".house-style.json": json.dumps({"ports": {"base": 15000}})})
    m = findings(
        tmp_path, {**full_stack(), "docker-compose.yml": 'services:\n  a:\n    ports: ["15002:80", "15500:80"]\n'}
    )
    assert "[15500] are outside this project's block 15000-15009" in m


def test_workspace_collisions(tmp_path):
    ws = tmp_path / "ws"
    write(
        ws,
        {
            "mine/docker-compose.yml": COMPOSE,
            "other/docker-compose.yml": 'services:\n  x:\n    ports: ["12000:80"]\n',
            "third/docker-compose.yml": 'services:\n  x:\n    ports: ["13000:80"]\n',
        },
    )
    m = " | ".join(project.check_project(ws / "mine", workspace=ws))
    assert "ports [12000] also claimed by project 'other'" in m
    assert "third" not in m
    write(ws, {"mine/.house-style.json": json.dumps({"ports": {"base": 13000}})})
    assert "'third'" in " | ".join(project.check_project(ws / "mine", workspace=ws))


def test_aws_requires_cdk_in_python(tmp_path):
    wf = {".github/workflows/deploy.yml": "uses: aws-actions/configure-aws-credentials@v4"}
    m = findings(tmp_path, {**wf, "a.txt": ""})
    assert "no cdk.json" in m
    ts = {**wf, "infra/cdk.json": "{}", "infra/package.json": json.dumps({"dependencies": {"aws-cdk-lib": "2"}})}
    assert "CDK app is TypeScript" in findings(tmp_path / "ts", ts)
    assert "not a Python dependency" in findings(
        tmp_path / "nopy", {"infra/cdk.json": "{}", "infra/pyproject.toml": '[project]\nname="i"\n'}
    )
    ok = findings(tmp_path / "ok", {"infra/cdk.json": "{}", "infra/requirements.txt": "aws-cdk-lib\n"})
    assert "CDK" not in ok.replace("cdk.json", "")


@pytest.mark.parametrize("name", ["serverless.yml", "samconfig.toml", "main.tf"])
def test_non_cdk_infrastructure_is_flagged(tmp_path, name):
    assert "non-CDK infrastructure" in findings(tmp_path, {f"infra/{name}": ""})


def test_e2e_required_for_full_stack(tmp_path):
    files = {k: v for k, v in full_stack().items() if k != "playwright.config.ts"}
    assert "no Playwright e2e" in findings(tmp_path, files)


def test_e2e_needs_mobile_project_and_axe(tmp_path):
    m = findings(tmp_path, {**full_stack(), "playwright.config.ts": "projects: [{ name: 'desktop' }]"})
    assert "no mobile project" in m
    web = json.dumps({"dependencies": {"next": "15"}, "devDependencies": {"eslint-config-next": "15"}})
    assert "@axe-core/playwright" in findings(tmp_path / "x", {**full_stack(), "web/package.json": web})
    assert "mobile" not in findings(
        tmp_path / "y", {**full_stack(), "playwright.config.ts": "viewport: { width: 390, height: 844 }"}
    )


def test_ignore_and_hidden_dirs_are_skipped(tmp_path):
    files = {"legacy/pyproject.toml": PY, ".cache/pkg/pyproject.toml": PY}
    assert "legacy" in findings(tmp_path, files)
    assert "legacy" not in " | ".join(project.check_project(tmp_path, ignore=("legacy",)))
    assert ".cache" not in " | ".join(project.check_project(tmp_path))


def test_walk_respects_depth(tmp_path):
    write(tmp_path, {"a/b/c/d/pyproject.toml": PY})
    assert [d.name for d, _ in project.walk(tmp_path, depth=3) if d.name == "d"] == []
    assert [d.name for d, _ in project.walk(tmp_path, depth=4) if d.name == "d"] == ["d"]


def test_read_missing_file_is_empty(tmp_path):
    assert project._read(tmp_path / "nope") == ""


# --- login / CORS references to local ports ---------------------------------------------------------------------
def test_stale_ports_in_login_and_cors_config(tmp_path):
    write(
        tmp_path,
        {
            "infra/stack.py": 'callback_urls=["http://localhost:3000/cb"]\n',
            "backend/settings.py": 'allow_origins = ["http://127.0.0.1:3000", "http://localhost:12000"]\n',
            "web/.env.example": "NEXT_PUBLIC_API_URL=http://localhost:8000\n",
            "docs/notes.md": "open http://localhost:3000 in your browser\n",  # no login/CORS context nearby
            "tests/test_cb.py": 'redirect = "http://localhost:3000"\n',  # tests are skipped
            "package-lock.json": '"redirect": "localhost:3000"',  # lockfiles are skipped
        },
    )
    refs = project.stale_port_refs(tmp_path, allowed={12000})
    joined = "\n".join(refs)
    assert "infra/stack.py:1" in joined
    assert "backend/settings.py:1" in joined
    assert "web/.env.example:1" in joined
    assert "notes.md" not in joined
    assert "tests/" not in joined
    assert "package-lock" not in joined
    assert "[3000]" in joined
    assert "[12000]" not in joined


def test_stale_port_refs_are_capped_and_skip_big_files(tmp_path):
    write(tmp_path, {f"s{i}.py": 'callback = "http://localhost:3000"\n' for i in range(15)})
    write(tmp_path, {"big.py": 'callback = "http://localhost:3000"\n' + "x" * 600_000})
    refs = project.stale_port_refs(tmp_path, allowed=set())
    assert len(refs) == project.MAX_REFS + 1
    assert "...and 3 more" in refs[-1]
    assert not any("big.py" in r for r in refs)


def test_stale_port_refs_survive_stat_errors(tmp_path, monkeypatch):
    write(tmp_path, {"a.py": 'callback = "http://localhost:3000"\n'})
    original = project.Path.stat

    def broken(self, *a, **kw):
        if self.name == "a.py":
            raise OSError("boom")
        return original(self, *a, **kw)

    monkeypatch.setattr(project.Path, "stat", broken)
    assert project.stale_port_refs(tmp_path, allowed=set()) == []


def test_project_check_reports_login_refs_only_with_a_compose_baseline(tmp_path):
    files = {**full_stack(), "infra/stack.py": 'callback_urls=["http://localhost:3000/cb"]\n'}
    assert "login/CORS: infra/stack.py:1" in findings(tmp_path, files)
    no_compose = {k: v for k, v in files.items() if k != "docker-compose.yml"}
    assert "login/CORS" not in findings(tmp_path / "n", no_compose)
    write(tmp_path / "b", {**files, ".house-style.json": json.dumps({"ports": {"base": 3000}})})
    assert "login/CORS" not in " | ".join(project.check_project(tmp_path / "b"))
