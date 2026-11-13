"""App wiring only: health, error handlers, routers. Domains live in sibling packages (see rules/backend.md)."""
import json
import logging
import sys

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PROBLEM = "application/problem+json"


class JsonFormatter(logging.Formatter):
    def format(self, r: logging.LogRecord) -> str:
        return json.dumps({"level": r.levelname, "logger": r.name, "msg": r.getMessage()})


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

app = FastAPI(title="API")


def problem(status: int, title: str, request: Request, **extra) -> JSONResponse:
    """RFC 9457 body. Pass `detail=...` and any extension members as keywords."""
    body = {"type": "about:blank", "title": title, "status": status, "instance": request.url.path, **extra}
    return JSONResponse(body, status_code=status, media_type=PROBLEM)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return problem(422, "Validation failed", request, errors=json.loads(json.dumps(exc.errors(), default=str)))


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}

# Domain errors: register one handler per domain base exception, mapping to problem(...), e.g.
# @app.exception_handler(NotFoundError) -> problem(404, "Not found", request, detail=str(exc))
