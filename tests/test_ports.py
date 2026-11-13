import importlib.util
import json

import ports
import pytest
from conftest import ROOT, write

spec = importlib.util.spec_from_file_location("ports_script", ROOT / "scripts" / "ports.py")
ports_script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ports_script)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('    ports:\n      - "3000:3000"\n', [3000]),
        ("    ports:\n      - 8000:8000\n", [8000]),
        ('      - "${API_PORT:-17061}:8000"\n', [17061]),
        ('      - "127.0.0.1:5432:5432"\n', [5432]),
        ("      - target: 80\n        published: 8080\n", [8080]),
        ('      - "8000-8010:8000-8010"\n', [8000]),
        ('    ports: ["${API_PORT:-17061}:8000", "9001:9000"]\n', [17061, 9001]),
        ("image: nginx\n", []),
    ],
)
def test_host_ports(text, expected):
    assert ports.host_ports(text) == expected


def test_compose_files_prunes_and_limits_depth(tmp_path):
    write(
        tmp_path,
        {
            "docker-compose.yml": "",
            "compose.yaml": "",
            "sub/docker-compose.e2e.yml": "",
            "a/b/c/docker-compose.yml": "",
            "node_modules/x/docker-compose.yml": "",
            "readme.md": "",
        },
    )
    names = {str(f.relative_to(tmp_path)) for f in ports.compose_files(tmp_path)}
    assert names == {"docker-compose.yml", "compose.yaml", "sub/docker-compose.e2e.yml"}


def test_project_ports_and_configured_base(tmp_path):
    write(
        tmp_path,
        {"docker-compose.yml": '    ports: ["12000:80"]\n', "sub/docker-compose.yml": '    ports: ["12001:80"]\n'},
    )
    assert ports.project_ports(tmp_path) == {12000, 12001}
    assert ports.configured_base(tmp_path) is None
    (tmp_path / ".house-style.json").write_text(json.dumps({"ports": {"base": 15000}}))
    assert ports.configured_base(tmp_path) == 15000
    (tmp_path / ".house-style.json").write_text("{broken")
    assert ports.configured_base(tmp_path) is None


def test_workspace_ports(tmp_path):
    write(
        tmp_path,
        {
            "a/docker-compose.yml": '    ports: ["12000:80"]\n',
            "b/.house-style.json": json.dumps({"ports": {"base": 14000}}),
            "c/readme.md": "",
            ".hidden/docker-compose.yml": '    ports: ["12999:80"]\n',
            "file.txt": "",
        },
    )
    found = ports.workspace_ports(tmp_path)
    assert set(found) == {"a", "b"}
    assert found["b"] == set(range(14000, 14010))
    assert set(ports.workspace_ports(tmp_path, exclude="a")) == {"b"}


def test_block_is_deterministic_and_in_range():
    base = ports.block_for("recap")
    assert base == ports.block_for("recap")
    assert ports.LOW <= base < ports.HIGH
    assert base % ports.SLOTS == 0


def test_block_skips_taken_ports():
    first = ports.block_for("recap")
    second = ports.block_for("recap", taken={first + 3})
    assert second != first
    assert not any(second <= p < second + ports.SLOTS for p in {first + 3})


def test_block_exhaustion_exits():
    with pytest.raises(SystemExit, match="no free port block"):
        ports.block_for("x", taken=set(range(ports.LOW, ports.HIGH)))


def test_default_ports_are_outside_the_project_range():
    assert not any(ports.LOW <= p < ports.HIGH for p in ports.DEFAULT_PORTS if p < ports.LOW or p >= ports.HIGH)
    assert 3000 in ports.DEFAULT_PORTS


def test_script_prints_and_writes_block(tmp_path, monkeypatch, argv, capsys):
    monkeypatch.chdir(tmp_path)
    argv("--name", "demo")
    assert ports_script.main() == 0
    out = capsys.readouterr().out
    assert "demo: block" in out
    assert not (tmp_path / ".house-style.json").exists()
    argv("--name", "demo", "--write")
    ports_script.main()
    base = json.loads((tmp_path / ".house-style.json").read_text())["ports"]["base"]
    assert f"web    {base}" in capsys.readouterr().out
    argv("--name", "other", "--write")  # an existing block is kept
    ports_script.main()
    assert json.loads((tmp_path / ".house-style.json").read_text())["ports"]["base"] == base


def test_script_avoids_workspace_ports(tmp_path, monkeypatch, argv, capsys):
    ws = tmp_path / "ws"
    mine = ws / "demo"
    mine.mkdir(parents=True)
    wanted = ports.block_for("demo")
    write(ws, {"other/docker-compose.yml": f'    ports: ["{wanted}:80"]\n'})
    monkeypatch.chdir(mine)
    argv("--name", "demo", "--workspace", ws, "--write")
    ports_script.main()
    assert json.loads((mine / ".house-style.json").read_text())["ports"]["base"] != wanted


def test_script_warns_about_login_when_moving_existing_ports(tmp_path, monkeypatch, argv, capsys):
    write(
        tmp_path,
        {
            "docker-compose.yml": '    ports: ["3000:3000"]\n',
            "infra/stack.py": 'callback_urls = ["http://localhost:3000/cb"]\n',
        },
    )
    monkeypatch.chdir(tmp_path)
    argv("--name", "demo")
    ports_script.main()
    out = capsys.readouterr().out
    assert "BREAK SIGN-IN" in out
    assert "infra/stack.py:1" in out


def test_script_warning_when_no_login_refs_found(tmp_path, monkeypatch, argv, capsys):
    write(tmp_path, {"docker-compose.yml": '    ports: ["3000:3000"]\n'})
    monkeypatch.chdir(tmp_path)
    argv("--name", "demo")
    ports_script.main()
    assert "still test a full sign-in" in capsys.readouterr().out
