import asyncio
import os

import httpx
from fastmcp import Client

os.environ.update(MCP_BASE_URL="https://mcp.example.com", OIDC_ISSUER="https://idp.example.com",
                  OIDC_JWKS_URI="https://idp.example.com/.well-known/jwks.json", OIDC_AUDIENCE="my-mcp")
from server import build, build_auth  # noqa: E402


def test_tool_in_memory():
    async def go():
        async with Client(build()) as c:
            return (await c.call_tool("ping", {})).data
    assert asyncio.run(go()) == "pong"


def test_discovery_and_401():
    app = build(build_auth()).http_app()

    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://mcp.example.com") as c:
            meta = await c.get("/.well-known/oauth-protected-resource/mcp")
            denied = await c.post("/mcp", json={})
            return meta, denied
    meta, denied = asyncio.run(go())
    assert meta.status_code == 200 and "https://idp.example.com/" in str(meta.json()["authorization_servers"])
    assert denied.status_code == 401
