import io
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
IDENT = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


@pytest.fixture(autouse=True)
def git_identity(monkeypatch):
    """CI runners have no git identity; tests that commit need one."""
    for k, v in IDENT.items():
        monkeypatch.setenv(k, v)


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def stdin(monkeypatch):
    def feed(payload):
        monkeypatch.setattr("sys.stdin", io.StringIO(payload if isinstance(payload, str) else json.dumps(payload)))

    return feed


@pytest.fixture
def argv(monkeypatch):
    def setv(*args):
        monkeypatch.setattr("sys.argv", ["prog", *map(str, args)])

    return setv


def write(root, files):
    """Create files from {relative path: text} under root."""
    for rel, text in files.items():
        f = Path(root) / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    return Path(root)
