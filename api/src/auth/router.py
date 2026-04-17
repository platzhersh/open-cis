from fastapi import APIRouter, Depends
from prisma.models import User

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the current authenticated user's profile."""
    return UserResponse.model_validate(current_user)
