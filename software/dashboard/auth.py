"""
WP25: Local admin authentication module.

Provides a lightweight bearer-token gate for all state-mutating API routes.
On first run, if SAIS_ADMIN_TOKEN is not set, a random token is generated
and printed to stdout for the operator to use.

Usage in routes:
    from auth import require_admin
    @app.post("/api/example")
    async def example(admin=Depends(require_admin)):
        ...
"""

import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

_bearer_scheme = HTTPBearer(auto_error=False)

def _get_admin_token() -> str:
    """Resolve the admin token from environment, generating one if absent."""
    token = os.environ.get("SAIS_ADMIN_TOKEN")
    if not token:
        token = secrets.token_urlsafe(32)
        os.environ["SAIS_ADMIN_TOKEN"] = token
        print("=" * 60)
        print("  SAIS Admin Token (auto-generated)")
        print(f"  {token}")
        print("  Set SAIS_ADMIN_TOKEN env var to use a fixed token.")
        print("=" * 60)
    return token

# Resolve once at import time
ADMIN_TOKEN = _get_admin_token()

async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency that enforces admin authentication.
    Checks Authorization: Bearer <token> header against SAIS_ADMIN_TOKEN.
    Returns the token string on success, raises 401 on failure.
    """
    if credentials is None or credentials.credentials != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required. Provide Authorization: Bearer <token>.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
