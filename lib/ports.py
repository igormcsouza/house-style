"""Fixed per-project port blocks. Stdlib only.
Each project owns a block of 10 consecutive host ports inside 10000-32759, below the Linux ephemeral range
(32768-60999) so they never collide with outgoing connections. Slots: web+0 api+1 db+2 queue+3 cache+4
aws/localstack+5 mcp+6 docs+7 e2e+8 spare+9."""

import fnmatch
import json
import os
import re
import zlib
from pathlib import Path

LOW, HIGH, SLOTS = 10000, 32760, 10
SLOT_NAMES = ("web", "api", "db", "queue", "cache", "aws", "mcp", "docs", "e2e", "spare")
DEFAULT_PORTS = {
    80,
    443,
    1433,
    3000,
    3001,
    3306,
    4000,
    4200,
    4566,
    5000,
    5173,
    5432,
    5672,
    6379,
    8000,
    8001,
    8008,
    8080,
    8081,
    8888,
    9000,
    9200,
    9229,
    15672,
    27017,
}
SKIP = {"node_modules", ".git", ".venv", "venv", ".next", "cdk.out", "worktrees", "dist", "build", "out", "site"}
COMPOSE_GLOBS = ("docker-compose*.y*ml", "compose*.y*ml")
ITEM = r"""["']?(?:[\d.]+:)?(?:\$\{[A-Za-z_]+:-(\d+)\}|(\d+))(?:-\d+)?:"""
SHORT = re.compile(r"^\s*-\s*" + ITEM, re.M)  # block list:  - "8000:8000"
INLINE = re.compile(r"ports:\s*\[([^\]]*)\]")  # flow list:   ports: ["8000:8000", "9000:9000"]
LONG = re.compile(r"published:\s*[\"']?(\d+)", re.M)


def compose_files(root, depth=2):
    """Compose files up to `depth` folders deep; prunes SKIP dirs while walking (never enters node_modules)."""
    root = Path(root)
    found = []
    for cur, dirs, files in os.walk(root):
        level = len(Path(cur).relative_to(root).parts)
        dirs[:] = [d for d in dirs if d not in SKIP] if level < depth else []
        found += [Path(cur) / f for f in files if any(fnmatch.fnmatch(f, p) for p in COMPOSE_GLOBS)]
    return sorted(found)


def host_ports(text):
    found = [int(a or b) for a, b in SHORT.findall(text)]
    for flow in INLINE.findall(text):
        found += [int(a or b) for item in flow.split(",") for a, b in re.findall(ITEM, item.strip())]
    return found + [int(p) for p in LONG.findall(text)]


def project_ports(root):
    ports = set()
    for f in compose_files(root):
        ports.update(host_ports(f.read_text(errors="ignore")))
    return ports


def configured_base(root):
    try:
        return int(json.loads((Path(root) / ".house-style.json").read_text())["ports"]["base"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def workspace_ports(workspace, exclude=None):
    """{project: set of claimed host ports} for every sibling project (compose files + configured block)."""
    out = {}
    for d in sorted(Path(workspace).iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name == exclude:
            continue
        claimed = project_ports(d)
        base = configured_base(d)
        if base:
            claimed |= set(range(base, base + SLOTS))
        if claimed:
            out[d.name] = claimed
    return out


def block_for(name, taken=()):
    """Deterministic block from the project name; probes the next block while any port is taken."""
    n = (HIGH - LOW) // SLOTS
    start = zlib.crc32(name.encode()) % n
    for k in range(n):
        base = LOW + ((start + k) % n) * SLOTS
        if not any(base <= p < base + SLOTS for p in taken):
            return base
    raise SystemExit("no free port block left")
