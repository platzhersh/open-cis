from fastapi import Depends, HTTPException, status

from src.auth.dependencies import get_current_user


def require_role(*allowed_roles: str):
    """Dependency that checks the current user has one of the allowed roles."""
    async def dependency(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return Depends(dependency)
