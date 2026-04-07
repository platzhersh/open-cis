import logging
import time

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from prisma.models import User

from src.config import settings
from src.db.client import prisma

logger = logging.getLogger(__name__)

security = HTTPBearer()

# JWKS cache with TTL
_jwks_cache: dict | None = None
_jwks_cache_time: float = 0
_JWKS_TTL_SECONDS = 3600  # 1 hour


async def _get_oidc_config() -> dict:
    """Fetch OIDC discovery document."""
    discovery_url = f"{settings.oidc_issuer}/.well-known/openid-configuration"
    async with httpx.AsyncClient() as client:
        response = await client.get(discovery_url, timeout=10)
        response.raise_for_status()
        return response.json()


async def _get_jwks() -> dict:
    """Fetch JWKS from the OIDC provider with TTL-based caching."""
    global _jwks_cache, _jwks_cache_time

    now = time.monotonic()
    if _jwks_cache is not None and (now - _jwks_cache_time) < _JWKS_TTL_SECONDS:
        return _jwks_cache

    config = await _get_oidc_config()
    jwks_uri = config["jwks_uri"]
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_uri, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_cache_time = now
        return _jwks_cache  # type: ignore[return-value]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Validate JWT Bearer token and return the authenticated User."""
    token = credentials.credentials
    try:
        jwks = await _get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.oidc_client_id,
        )
    except JWTError as e:
        logger.debug(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e
    except Exception as e:  # noqa: BLE001
        logger.error(f"OIDC validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e

    sub: str | None = payload.get("sub")
    email: str = payload.get("email", "")
    name: str = payload.get("name", email)

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub claim",
        )

    # Read-then-create: avoid writes on read paths
    user = await prisma.user.find_unique(where={"externalId": sub})
    if user is not None:
        return user

    # First login — check if a legacy user with this email exists (migration)
    if email:
        existing = await prisma.user.find_unique(where={"email": email})
        if existing is not None:
            user = await prisma.user.update(
                where={"id": existing.id},
                data={"externalId": sub, "name": name},
            )
            return user

    # Brand-new user
    user = await prisma.user.create(
        data={
            "externalId": sub,
            "email": email,
            "name": name,
            "role": "CLINICIAN",  # type: ignore[typeddict-item]
        }
    )
    return user
