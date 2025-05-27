"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.controllers.auth_controller import (
    authenticate_user,
    create_user,
    get_current_active_user,
    get_user_profile,
    update_user_profile,
    delete_user_account
)
from app.core.database import get_db
from app.schemas.auth_schemas import (
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate
)
from app.models.user import User

router = APIRouter(
    tags=["auth"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid authentication credentials"
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not enough privileges"
        }
    }
)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Create new user."""
    return await create_user(db, user_data)

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Authenticate user and return token."""
    return await authenticate_user(db, login_data)

@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """Get current user profile."""
    return await get_user_profile(current_user)

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Update current user profile."""
    return await update_user_profile(db, current_user, update_data)

@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete current user account."""
    await delete_user_account(db, current_user)
