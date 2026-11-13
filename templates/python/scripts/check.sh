#!/usr/bin/env bash
# The one command CI and humans run before a PR.
set -euo pipefail
cd "$(dirname "$0")/.."
uv run ruff check .
uv run ruff format --check .
uv run pytest
