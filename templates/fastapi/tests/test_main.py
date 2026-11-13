from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_healthz():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_validation_is_problem_json():
    app.add_api_route("/x", lambda n: n, methods=["GET"])  # `n` is a required query param -> 422
    r = client.get("/x")
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["title"] == "Validation failed"


def test_environment_defaults_to_local(monkeypatch):
    from src.core.config import environment

    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert environment() == "local"
    monkeypatch.setenv("ENVIRONMENT", "prod")
    assert environment() == "prod"
