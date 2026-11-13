# Python standard

- **uv only.** `pyproject.toml` + `uv.lock` committed; `uv sync`, `uv run`, `uv add`. No `requirements.txt`, Pipfile, Poetry, `pip install`. Docker images install with `uv sync --frozen --no-dev`.
- **pytest only, 100% coverage enforced.** `[tool.pytest.ini_options] addopts = "--cov=src --cov-fail-under=100"` (or `[tool.coverage.report] fail_under = 100`). Tests are plain functions + fixtures, mirror `src/`, never `unittest.TestCase` (`unittest.mock` is fine). Only truly unreachable lines get `# pragma: no cover`, with a reason. CI fails below 100.
- **Lint/format:** ruff with `templates/python/ruff.toml` (correctness, bandit `S` security, complexity <= 10, args <= 6, dead code, blind except). `ruff check` + `ruff format --check` in the check script.
- **Smells to refuse:** functions over ~50 statements or complexity > 10, > 6 parameters, commented-out code, blind `except`/`pass`, global mutable state, circular imports, business rules in controllers, a service importing a controller, duplicated logic across domains (extract to `shared/`).
- **Types:** annotate public functions; Pydantic models at the edges, no raw dicts across layers.
- **Project layout:** FastAPI projects follow `rules/backend.md` (domain packages). Scripts under `scripts/`, one command to run everything: `make check` or `./scripts/check.sh`.
Audit: `/house-style:audit --deep` runs ruff (with this config) and pip-audit.
