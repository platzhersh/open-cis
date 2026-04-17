import logging

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from prisma.models import User

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserResponse
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the current authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.post("/token")
async def proxy_token_exchange(request: Request) -> JSONResponse:
    """Proxy the OIDC token exchange to Dex to avoid browser CORS issues."""
    body = await request.body()
    token_url = settings.oidc_token_url or f"{settings.oidc_issuer}/token"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                content=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
    except httpx.HTTPError as e:
        logger.error(f"Token exchange failed: {type(e).__name__}: {e} (url={token_url})")
        return JSONResponse(
            status_code=502,
            content={"error": "OIDC provider unreachable"},
        )

    try:
        content = response.json()
    except (ValueError, UnicodeDecodeError):
        content = {"error": response.text}

    return JSONResponse(
        status_code=response.status_code,
        content=content,
    )
