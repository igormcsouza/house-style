# Contributing

## Develop

```bash
uv sync && uv run ruff check . && uv run ruff format --check . && uv run pytest
claude plugin validate .
python3 scripts/audit.py . --ignore templates
```

`pytest` enforces 100% coverage. Tests are pytest only, in-process and hermetic (no network, fake external tools). Python is stdlib only in hooks, scripts and lib.

## Add a rule

1. Text in `rules/` (keep `core.md` short: it costs tokens every session).
2. A check in `lib/checks.py` (per file) or `lib/project.py` (per project) when it is machine-checkable.
3. A test.

## Add an accent

One line in `lib/tokens.py` `ACCENTS`, then `python3 scripts/build.py --check` validates contrast.

## Templates

Scaffolds in `templates/` carry their own dependencies and tests:

```bash
cd templates/fastapi && uv sync && uv run pytest && uv run ruff check --config ../python/ruff.toml .
```

Same for `fastmcp` and `cdk`.

## Docs site

```bash
uv run --group docs mkdocs serve
uv run --group docs mkdocs build --strict
```

`docs/standard/` is a symlink to `rules/`: the standard is written once and published as-is. CI deploys to GitHub Pages on push to `main`.

## Conventions

Conventional Commits, `feat/...` branches, releases through `scripts/release.py`. `plugin.json` has no `version` on purpose: every commit on `main` is a new plugin version.
