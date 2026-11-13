# MCP servers: standalone FastMCP + OAuth auto-discovery

Use the standalone `fastmcp` package: `from fastmcp import FastMCP`. NOT `mcp.server.fastmcp` (the SDK's older copy).
Auth is attached with `FastMCP(name, auth=provider)`; it only applies to HTTP transports (stdio/in-memory are unauthenticated). Serve with `mcp.run(transport="http")` or `mcp.http_app()` for ASGI/Lambda.

Choose the provider by what your IdP supports:
| IdP | Provider |
|---|---|
| Supports DCR + JWTs (WorkOS AuthKit, Descope, a DCR-capable Cognito/Citadel front) | `RemoteAuthProvider(token_verifier=JWTVerifier(...), authorization_servers=[...], base_url=...)`. Serves `/.well-known/oauth-protected-resource`, so clients auto-detect the IdP |
| No DCR (GitHub, Google, Azure, plain Cognito app client) | `OAuthProxy` or a built-in subclass (e.g. `GitHubProvider`): presents DCR to clients, uses your pre-registered upstream credentials |
| Token check only, no discovery | `JWTVerifier` / `TokenVerifier` directly |
| You are the authorization server | `OAuthProvider` (last resort) |
Imports: `fastmcp.server.auth` (`RemoteAuthProvider`, `OAuthProxy`), `fastmcp.server.auth.providers.jwt` (`JWTVerifier`).

Rules
- Never hand-roll `/.well-known/oauth-*` routes or token validation (the guard hook flags `custom_route("/.well-known/oauth...")`). If FastMCP lacks a case, open the gap upstream or isolate a documented shim.
- Config from env: `MCP_BASE_URL` (no `/mcp` suffix), `OIDC_ISSUER`, `OIDC_JWKS_URI`, `OIDC_AUDIENCE`. Secrets never in code.
- Validate issuer + audience + expiry always; require scopes per tool when sensitive.
- Tools: typed args, docstring = the description the model reads, small outputs, `ToolError` for user-facing failures, `readOnlyHint`/`destructiveHint` annotations.
- Test: in-memory `Client(mcp)` for tools; ASGI GET of `/.well-known/oauth-protected-resource/mcp` + 401 on missing token for auth.
- Clients (local CLIs) use Authorization Code + PKCE with loopback redirect (see draftr-mcp/auth.py).
Template: `templates/fastmcp`. Verify details against https://gofastmcp.com/servers/auth/authentication when upgrading FastMCP.
