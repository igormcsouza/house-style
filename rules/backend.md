# Backend standard (FastAPI)

Layout (from Cashlytics, the reference): domain packages, never global `models/ services/ controllers/` folders.
```
backend/src/
  main.py        # app, CORS, /healthz, routers, exception handlers only
  core/config.py # env-only config; core/logging.py
  shared/        # Repository Protocol + generic implementation
  <domain>/{models,exceptions,repositories,services,controllers}.py
backend/lambda_function.py  # Lambda handler at root (Mangum)
```
- Thin controllers: parse, call service, map domain exceptions to HTTP. Services own rules, depend on a `Protocol`, not a concrete repo.
- Config: environment variables only (`ENVIRONMENT`, `AWS_REGION`, ...). No config files with secrets.
- Errors: RFC 9457 `application/problem+json` (`type,title,status,detail,instance`), one handler for domain exceptions, one for validation. Never leak stack traces.
- Logging: JSON lines to stdout with request id; no PII/tokens.
- Health: `GET /healthz` (liveness, no deps) and `GET /readyz` (deps) when needed.
- Auth: validate JWT (issuer, audience, expiry, JWKS) in one dependency; scope checks per route. Cognito/Citadel are the IdPs already in use.
- Tooling: `uv`, `ruff check` + `ruff format`, pytest with `--cov-fail-under=100`, tests mirror `src/`. `./scripts/check.sh` or `make check` runs everything. Infra: CDK (Python).
- API: plural nouns, `/api/v1`, cursor pagination, ISO-8601 UTC, idempotency key on unsafe retries, 201+Location on create.
Template: `templates/fastapi`.
