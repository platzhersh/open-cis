import logging
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config import settings
from src.db.client import prisma

logger = logging.getLogger(__name__)

security = HTTPBearer()


@lru_cache(maxsize=1)
def _get_oidc_config() -> dict:
    """Fetch OIDC discovery document (cached)."""
    discovery_url = f"{settings.oidc_issuer}/.well-known/openid-configuration"
    response = httpx.get(discovery_url, timeout=10)
    response.raise_for_status()
    return response.json()


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """Fetch JWKS from the OIDC provider (cached)."""
    config = _get_oidc_config()
    jwks_uri = config["jwks_uri"]
    response = httpx.get(jwks_uri, timeout=10)
    response.raise_for_status()
    return response.json()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Validate JWT Bearer token and return the authenticated User."""
    token = credentials.credentials
    try:
        jwks = _get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},
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

    sub = payload.get("sub")
    email = payload.get("email", "")
    name = payload.get("name", email)

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub claim",
        )

    # Upsert user on first login
    user = await prisma.user.upsert(
        where={"externalId": sub},
        data={
            "create": {
                "externalId": sub,
                "email": email,
                "name": name,
                "role": "CLINICIAN",  # type: ignore[typeddict-item]  # Prisma accepts string for enum
            },
            "update": {
                "email": email,
                "name": name,
            },
        },
    )
    return user
