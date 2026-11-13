# Security standard

- **Secrets**: only in the environment or a secret manager; `.env` is git-ignored, `.env.example` committed with fake values. The guard hook blocks hard-coded secrets; never log tokens/PII.
- **Authn/z**: validate JWT issuer, audience, expiry and signature (JWKS) in ONE dependency; scopes per route; deny by default. OAuth per `rules/mcp-oauth.md`. Passwords: argon2/bcrypt, never md5/sha1.
- **Input**: Pydantic models with explicit types and bounds on every request body/query; no `eval`/`exec`; no `shell=True`; no string-built SQL (bound parameters); no `pickle`/unsafe `yaml.load`.
- **HTTP**: CORS lists real origins (never `*` with credentials); security headers (HSTS, CSP, X-Content-Type-Options, frame-ancestors); rate limit auth endpoints; request size limits; errors as problem+json without stack traces.
- **Dependencies**: `uv.lock`/`package-lock.json` committed; `pip-audit` (`/house-style:audit --deep`) and `npm audit` in CI; Dependabot/Renovate on; pin Docker base tags.
- **Containers/infra**: non-root user, read-only root FS where possible, no secrets in images; CDK least privilege, encryption on, no public buckets; OIDC for CI to AWS.
- **Frontend**: no secrets in client bundles (only public env), sanitize rendered HTML, `rel="noopener"` on external links, CSP compatible.
