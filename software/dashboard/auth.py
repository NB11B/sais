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

# WP25.2: Production hardening. Disable fallback to ADMIN_TOKEN if SAIS_ENV=production.
SAIS_ENV = os.environ.get("SAIS_ENV", "development").lower()
NODE_TOKEN = os.environ.get("SAIS_NODE_TOKEN")

if not NODE_TOKEN:
    if SAIS_ENV == "production":
        # In production, we MUST have a separate node token. 
        # If not set, we use a different random one to prevent admin token reuse.
        NODE_TOKEN = secrets.token_urlsafe(32)
        print("!" * 60)
        print("  WARNING: SAIS_ENV=production but SAIS_NODE_TOKEN not set.")
        print("  Generated a random NODE_TOKEN to prevent Admin Token fallback.")
        print(f"  NODE_TOKEN: {NODE_TOKEN}")
        print("!" * 60)
    else:
        # Development fallback
        NODE_TOKEN = ADMIN_TOKEN

async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency that enforces admin authentication.
    Checks Authorization: Bearer <token> header against SAIS_ADMIN_TOKEN.
    Returns the token string on success, raises 401 on failure.
    """
    if credentials is None or not secrets.compare_digest(credentials.credentials, ADMIN_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required. Provide Authorization: Bearer <token>.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

async def require_node_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency that enforces node authentication.
    Allows either ADMIN_TOKEN or NODE_TOKEN.
    In production mode, the tokens must be distinct.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Node authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_val = credentials.credentials
    is_admin = secrets.compare_digest(token_val, ADMIN_TOKEN)
    is_node = secrets.compare_digest(token_val, NODE_TOKEN)
    
    # In production, we reject the admin token for node routes to prevent token leakage
    # if a node is compromised.
    if is_admin and SAIS_ENV == "production" and not is_node:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin token cannot be used for node operations in production.",
        )
    
    if not (is_admin or is_node):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid node or admin token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_val
