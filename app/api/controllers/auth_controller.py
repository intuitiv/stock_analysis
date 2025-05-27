"""Authentication controller."""
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user as get_current_user_security
from app.models.user import User
from app.schemas.auth_schemas import (
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate
)
from app.services.user_service import UserService

async def create_user(db: AsyncSession, user_data: UserCreate) -> UserResponse:
    """Create new user."""
    return await UserService.create_user(db, user_data)

async def authenticate_user(db: AsyncSession, login_data: UserLogin) -> Token:
    """Authenticate user."""
    return await UserService.authenticate_user(db, login_data)

async def get_current_active_user(
    current_user: User = Depends(get_current_user_security)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_user_profile(current_user: User) -> UserResponse:
    """Get user profile."""
    return current_user

async def update_user_profile(
    db: AsyncSession,
    current_user: User,
    update_data: UserUpdate
) -> UserResponse:
    """Update user profile."""
    return await UserService.update_user(db, current_user, update_data)

async def delete_user_account(db: AsyncSession, current_user: User) -> None:
    """Delete user account."""
    await UserService.delete_user(db, current_user)
