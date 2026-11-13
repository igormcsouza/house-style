"""Project-level standards: uv, pytest + 100% coverage, vitest coverage, FastAPI layout, Docker Compose, ports,
CDK (Python), Playwright e2e. Static and deterministic. Stdlib only. check_project(root) -> [message]."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import ports

SKIP = ports.SKIP | {
    "__pycache__",
    "coverage",
    "playwright-report",
    "test-results",
    ".expo",
    "android",
    "ios",
    "templates",
}
GLOBAL_LAYERS = {"models", "services", "controllers", "schemas", "routers", "repositories"}
NON_UV = ("requirements.txt", "requirements-dev.txt", "requirements.in", "Pipfile", "Pipfile.lock", "poetry.lock")
WEB = re.compile(r'"(next|react-dom|react)"\s*:')
MOBILE_VIEWPORT = re.compile(r"devices\[|isMobile|viewport\s*:\s*\{[^}]*width\s*:\s*(3\d\d|4[0-3]\d)\b")


def walk(root, depth=3, ignore=()):
    """Yield (dir, files) up to `depth` levels, pruning skipped dirs. `ignore` = extra folder names."""
    root = Path(root)
    skip = SKIP | set(ignore)
    for cur, dirs, files in os.walk(root):
        level = len(Path(cur).relative_to(root).parts)
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")] if level < depth else []
        yield Path(cur), files


def _read(p):
    try:
        return Path(p).read_text(errors="ignore")
    except OSError:
        return ""


def _gate_100(text):
    return bool(re.search(r"--cov-fail-under[= ]+100\b|fail[-_]under\s*=\s*100\b", text))


def _python(root, d, files, out):
    rel = d.relative_to(root) or Path(".")
    text = _read(d / "pyproject.toml")
    if "uv.lock" not in files:
        out.append(f"{rel}: uv.lock missing (Python projects use uv)")
    bad = [f for f in files if f in NON_UV] + (["[tool.poetry]"] if "[tool.poetry]" in text else [])
    if bad:
        out.append(f"{rel}: not uv ({', '.join(bad)}); migrate dependencies to pyproject.toml + uv.lock")
    has_tests = (d / "tests").is_dir() or "pytest" in text
    cov = text + _read(d / ".coveragerc") + _read(d / "setup.cfg")
    if not has_tests:
        out.append(f"{rel}: no tests (pytest, 100% coverage)")
    elif not _gate_100(cov):
        out.append(
            f"{rel}: coverage gate missing or below 100 (pytest --cov-fail-under=100 or [tool.coverage.report] fail_under = 100)"
        )
    if re.search(r"fastapi", text, re.I):
        for base in ("src", "app"):
            for layer in sorted(GLOBAL_LAYERS):
                if (d / base / layer).is_dir():
                    out.append(
                        f"{rel}/{base}/{layer}/: global layer folder; use domain packages (src/<domain>/models.py, services.py, ...)"
                    )


def _frontend(root, d, files, out):
    rel = d.relative_to(root) or Path(".")
    pkg = _read(d / "package.json")
    configs = [f for f in files if re.match(r"(vitest|vite|jest)\.config\.", f)]
    cfg = "".join(_read(d / f) for f in configs) + pkg
    if not configs and '"jest"' not in pkg and '"vitest"' not in pkg:
        out.append(f"{rel}: no unit-test runner (vitest for web; jest-expo is fine for Expo) with coverage at 100")
    elif not re.search(
        r"thresholds\s*:\s*\{[^}]*(100\s*:\s*true|lines\s*:\s*100)|coverageThreshold", cfg, re.S
    ) or re.search(r"(lines|statements|functions|branches)\s*:\s*(?!100\b)\d+", cfg):
        out.append(
            f"{rel}: coverage thresholds missing or below 100 (vitest `coverage.thresholds: {{ 100: true }}`; jest `coverageThreshold`)"
        )
    if '"next"' in pkg and "jsx-a11y" not in pkg and "eslint-config-next" not in pkg:
        out.append(f"{rel}: no jsx-a11y lint (eslint-config-next or eslint-plugin-jsx-a11y)")


LOCAL_PORT = re.compile(r"(?:localhost|127\.0\.0\.1):(\d{2,5})")
AUTH_CONTEXT = re.compile(
    r"(?i)callback|redirect|logout|sign.?out|cors|allow_?origins?|allowed_?origins?|cognito|oauth|issuer|base_?url|api_?url|origin"
)
SCAN_EXT = {".py", ".ts", ".tsx", ".js", ".mjs", ".json", ".yml", ".yaml", ".toml", ".md", ".env", ".example"}
NO_SCAN = {"package-lock.json", "uv.lock", "pnpm-lock.yaml", "yarn.lock", "tsconfig.json"}
MAX_REFS = 12
MAX_SCAN_BYTES = 512_000
NON_CDK_FILES = ("serverless.yml", "serverless.yaml", "samconfig.toml")


def stale_port_refs(root, allowed, ignore=()):
    """Login/CORS-related lines that mention a local port outside `allowed`.
    Moving a project to its fixed port block silently breaks sign-in when Cognito/OAuth callback and logout URLs,
    CORS origins or base URLs still name the old ports. Returns human-readable findings."""
    root, found = Path(root), []
    for d, files in walk(root, depth=4, ignore=set(ignore) | {"tests", "__tests__"}):
        for name in files:
            f = d / name
            if (
                name in NO_SCAN
                or name.startswith("docker-compose")
                or (f.suffix not in SCAN_EXT and not name.startswith(".env"))
            ):
                continue
            try:
                if f.stat().st_size > MAX_SCAN_BYTES:
                    continue
            except OSError:
                continue
            lines = _read(f).splitlines()
            for i, line in enumerate(lines):
                bad = sorted({int(p) for p in LOCAL_PORT.findall(line)} - set(allowed))
                if bad and AUTH_CONTEXT.search("\n".join(lines[max(0, i - 2) : i + 3])):
                    found.append(
                        f"login/CORS: {f.relative_to(root)}:{i + 1} names local port(s) {bad}; update Cognito/OAuth callback + logout URLs, CORS origins, base URLs and redeploy"
                    )
    return found[:MAX_REFS] + (
        [f"login/CORS: ...and {len(found) - MAX_REFS} more references"] if len(found) > MAX_REFS else []
    )


def _ports(root, files_by_dir, out, workspace):
    for f in ports.compose_files(root):
        rel = f.relative_to(root)
        host = ports.host_ports(_read(f))
        bad_default = sorted(p for p in host if p in ports.DEFAULT_PORTS)
        bad_range = sorted(p for p in host if not ports.LOW <= p < ports.HIGH and p not in ports.DEFAULT_PORTS)
        if bad_default:
            out.append(
                f"{rel}: default host ports {bad_default} collide with other projects; use your block (scripts/ports.py)"
            )
        if bad_range:
            out.append(
                f"{rel}: host ports {bad_range} outside {ports.LOW}-{ports.HIGH - 1} (Linux uses 32768+ for outgoing connections)"
            )
    base = ports.configured_base(root)
    if base:
        own = [p for f in ports.compose_files(root) for p in ports.host_ports(_read(f))]
        stray = sorted({p for p in own if not base <= p < base + ports.SLOTS})
        if stray:
            out.append(
                f".house-style.json: ports {stray} are outside this project's block {base}-{base + ports.SLOTS - 1}"
            )
    if workspace:
        mine = ports.project_ports(root) | (set(range(base, base + ports.SLOTS)) if base else set())
        for other, theirs in ports.workspace_ports(workspace, exclude=Path(root).resolve().name).items():
            clash = sorted(mine & theirs)
            if clash:
                out.append(f"ports {clash} also claimed by project '{other}'")


@dataclass
class Facts:
    py_dirs: list = field(default_factory=list)
    pkg_dirs: list = field(default_factory=list)
    has_cdk_json: bool = False
    fastapi: bool = False
    web: bool = False
    mobile: bool = False

    @property
    def front(self):
        return self.web or self.mobile


def _scan(root, ignore, out):
    """Walk the project once: run the per-directory checks and collect what the project is made of."""
    facts = Facts()
    for d, files in walk(root, ignore=ignore):
        if "pyproject.toml" in files:
            _python(root, d, files, out)
            facts.py_dirs.append(d)
            facts.fastapi = facts.fastapi or bool(re.search(r"fastapi", _read(d / "pyproject.toml"), re.I))
        elif any(f in NON_UV for f in files) and any(f.endswith(".py") for f in files):
            out.append(f"{d.relative_to(root) or '.'}: Python without pyproject.toml/uv; use uv")
        pkg = _read(d / "package.json") if "package.json" in files else ""
        if WEB.search(pkg) or '"expo"' in pkg:
            _frontend(root, d, files, out)
            facts.pkg_dirs.append(d)
            facts.web = facts.web or bool(re.search(r'"(next|react-dom)"', pkg))
            facts.mobile = facts.mobile or '"expo"' in pkg
        facts.has_cdk_json = facts.has_cdk_json or "cdk.json" in files
    return facts


def _aws(root, facts, ignore, out):
    """Deploying to AWS means CDK in Python."""
    workflows = root / ".github" / "workflows"
    wf = "".join(_read(f) for f in workflows.glob("*.y*ml")) if workflows.is_dir() else ""
    if not ("aws-actions/configure-aws-credentials" in wf or (root / "infra").is_dir() or facts.has_cdk_json):
        return
    dirs = [d for d, _ in walk(root, ignore=ignore)]
    py_cdk = any("aws-cdk-lib" in _read(d / "pyproject.toml") + _read(d / "requirements.txt") for d in dirs)
    ts_cdk = any('"aws-cdk-lib"' in _read(d / "package.json") for d in dirs)
    if not facts.has_cdk_json:
        out.append("deploys to AWS but has no cdk.json: use AWS CDK in Python")
    elif ts_cdk and not py_cdk:
        out.append("CDK app is TypeScript: use CDK in Python (aws-cdk-lib in pyproject.toml)")
    elif not py_cdk:
        out.append("cdk.json present but aws-cdk-lib is not a Python dependency")


def _non_cdk_infra(root, ignore, out):
    for d, files in walk(root, ignore=ignore):
        out += [
            f"{(d / f).relative_to(root)}: non-CDK infrastructure; use AWS CDK in Python"
            for f in files
            if f in NON_CDK_FILES or f.endswith(".tf")
        ]


def _e2e(root, facts, ignore, out):
    """Frontend + backend + infra => Playwright e2e on a mobile viewport with axe."""
    if not (facts.front and facts.fastapi and facts.has_cdk_json):
        return
    configs = [d / f for d, files in walk(root, ignore=ignore) for f in files if f.startswith("playwright.config.")]
    if not configs:
        out.append("frontend + backend + infra but no Playwright e2e (playwright.config.ts, templates/e2e)")
        return
    if not MOBILE_VIEWPORT.search("".join(_read(f) for f in configs)):
        out.append("Playwright config has no mobile project (devices['Pixel 7'] or a 375-430px viewport)")
    if not any("@axe-core/playwright" in _read(d / "package.json") for d in facts.pkg_dirs):
        out.append("no @axe-core/playwright: add an accessibility scan to the e2e suite")


def check_project(root, workspace=None, ignore=()):
    root = Path(root).resolve()
    out = []
    facts = _scan(root, ignore, out)
    compose = ports.compose_files(root)
    if (facts.front or facts.fastapi) and not compose:
        out.append("no docker-compose.yml: the app must run with `docker compose up`")
    _ports(root, None, out, workspace)
    own = ports.project_ports(root)
    base = ports.configured_base(root)
    if base:
        own |= set(range(base, base + ports.SLOTS))
    if compose and own:
        out += stale_port_refs(root, own, ignore)
    _aws(root, facts, ignore, out)
    _non_cdk_infra(root, ignore, out)
    _e2e(root, facts, ignore, out)
    return out
