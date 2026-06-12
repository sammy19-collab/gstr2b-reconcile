from typing import List
from fastapi import Depends, HTTPException, status
from app.dependencies import get_current_user
from app.models.user import User


def require_role(*roles: str):
    """Dependency factory: require one of the given roles."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role.value} does not have permission. Required: {list(roles)}",
            )
        return current_user

    return dependency
