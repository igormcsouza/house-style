"""MCP server: standalone FastMCP + OAuth with auto-discovery. Config is env-only.
Run: `uv run python server.py` (HTTP on :8000/mcp). Env: MCP_BASE_URL, OIDC_ISSUER, OIDC_JWKS_URI, OIDC_AUDIENCE."""
import os

from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from pydantic import AnyHttpUrl


def build_auth() -> RemoteAuthProvider:
    # RemoteAuthProvider fits an IdP that supports DCR + JWTs. For IdPs without DCR (GitHub, Google, plain
    # Cognito app client) swap in OAuthProxy / a built-in provider. See rules/mcp-oauth.md.
    verifier = JWTVerifier(
        jwks_uri=os.environ["OIDC_JWKS_URI"],
        issuer=os.environ["OIDC_ISSUER"],
        audience=os.environ["OIDC_AUDIENCE"],
    )
    return RemoteAuthProvider(
        token_verifier=verifier,
        authorization_servers=[AnyHttpUrl(os.environ["OIDC_ISSUER"])],
        base_url=os.environ["MCP_BASE_URL"],  # no /mcp suffix
    )


def build(auth=None) -> FastMCP:
    mcp = FastMCP("my-server", auth=auth)

    @mcp.tool
    def ping() -> str:
        """Health check: returns 'pong'."""
        return "pong"

    return mcp


if __name__ == "__main__":
    build(build_auth()).run(transport="http", host="0.0.0.0", port=8000)
