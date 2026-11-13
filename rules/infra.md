# Infrastructure, Docker and ports

## AWS => CDK in Python
- Deploying to AWS means AWS CDK **in Python** (`infra/`, `cdk.json`, `aws-cdk-lib` in `pyproject.toml`, managed with uv). No TypeScript CDK, Terraform, Serverless, SAM or hand-written CloudFormation.
- One stack per concern; config from env/context, never hard-coded account ids or secrets; least-privilege IAM (no `*` actions/resources); encryption on, public access off by default; removal policy explicit; tags on every stack.
- Tests: CDK assertions (`Template.from_stack`) for IAM, public exposure and resource counts, counted in the 100% gate. Prod deploys are a hard stop (user OK); GitHub Actions use OIDC, no stored AWS keys.

## Everything runs with Docker Compose
- `docker-compose.yml` at the root brings the whole app up with ONE command (`docker compose up`): api, web, db/localstack, mocks for auth. No manual steps beyond copying `.env.example`.
- Images: multi-stage, non-root user, pinned base tags, `.dockerignore`, healthchecks, `uv sync --frozen` for Python.
- Compose reads ports from env with fixed defaults from the project block (below). Never the popular defaults.

## Ports: every project owns a fixed block
- Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ports.py --workspace <parent of your projects> --write` once (`/house-style:init` does it). It derives 10 consecutive ports from the project name inside **10000-32759** (below Linux's 32768+ ephemeral range), skips blocks other projects already claim, and stores `{"ports": {"base": N}}` in `.house-style.json`.
- Slots: web +0, api +1, db +2, queue +3, cache +4, aws/localstack +5, mcp +6, docs +7, e2e +8, spare +9.
- Compose: `ports: ["${WEB_PORT:-<base+0>}:3000"]`. The container-side port may stay 3000/8000; only the HOST side changes.
- Banned host ports: 80, 443, 3000, 3001, 4000, 4200, 4566, 5000, 5173, 5432, 5672, 6379, 8000, 8001, 8080, 8081, 8888, 9000, 9200, 15672, 27017 and anything outside the range. The audit flags them and reports collisions across your projects.

## Changing the ports of an existing project: review LOGIN first
Moving to the fixed block is a one-line compose change that can silently break sign-in: identity providers (Cognito, OAuth) only accept redirect addresses registered in advance, so a new port causes a "redirect mismatch" while the app itself looks fine.
1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ports.py --workspace <projects dir> --write` in the project: it lists every login/CORS line that still names a local port (`audit` does the same under "project standards").
2. Update, in this order: Cognito/OAuth **callback and logout URLs** in the CDK stack (register the new URLs; keep the old ones until sign-in is verified, then remove them), CORS allowed origins, `*_BASE_URL`/`API_URL`/issuer settings, `.env.example`, e2e `baseURL`, README/docs.
3. CLI/loopback logins (e.g. a local tool opening `http://localhost:PORT/callback`) use a fixed port inside the block (mcp slot +6) and register it the same way.
4. Redeploying the CDK stack is a hard stop: show the user the callback/logout diff and get their OK before deploying.
5. Verify a full sign-in end to end (the e2e suite should cover login) before declaring the move done.
Never change a project's ports without telling the user which login settings are affected.
