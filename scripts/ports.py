#!/usr/bin/env python3
"""Pick (and optionally record) this project's fixed port block.
  ports.py [--name N] [--workspace ~/Projects] [--write]
Prints the slots. --write stores {"ports": {"base": N}} in .house-style.json. Re-running keeps an existing block."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import ports
import project


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", default=Path.cwd().name)
    p.add_argument("--workspace", help="parent dir holding your other projects (collision-aware)")
    p.add_argument("--write", action="store_true")
    a = p.parse_args()
    cfg_file = Path(".house-style.json")
    cfg = json.loads(cfg_file.read_text()) if cfg_file.is_file() else {}
    base = ports.configured_base(".")
    if base is None:
        taken = set().union(*ports.workspace_ports(a.workspace, exclude=a.name).values()) if a.workspace else set()
        base = ports.block_for(a.name, taken)
        if a.write:
            cfg["ports"] = {"base": base}
            cfg_file.write_text(json.dumps(cfg, indent=2) + "\n")
    print(f"{a.name}: block {base}-{base + ports.SLOTS - 1}")
    for i, slot in enumerate(ports.SLOT_NAMES):
        print(f"  {slot:6} {base + i}")
    old = ports.project_ports(".")
    if old - set(range(base, base + ports.SLOTS)):
        print(
            f"\nWARNING: this project currently publishes {sorted(old)}. Moving to the block above can BREAK SIGN-IN."
        )
        print(
            "Review login BEFORE changing compose (callback/logout URLs in CDK, CORS origins, base URLs, e2e baseURL, docs):"
        )
        refs = project.stale_port_refs(".", set(range(base, base + ports.SLOTS)))
        print(
            "\n".join(f"  - {r}" for r in refs)
            or "  (no login/CORS references to local ports found; still test a full sign-in)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
