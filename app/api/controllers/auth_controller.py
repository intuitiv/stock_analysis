from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm # For standard token endpoint
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db # Standard way to get DB session in FastAPI
from app.services.user_service import UserService
from app.schemas.auth_schemas import UserCreate, UserResponse, Token, UserLogin
from app.core.security import create_access_token, get_current_active_user
from app.models.user import User as UserModel

router = APIRouter()

# Instantiate UserService here or use a dependency provider if you prefer
# For simplicity in this context, direct instantiation or a simple factory.
# A more robust DI system would be better for larger apps.
# user_service_instance = UserService() # This won't work if UserService needs db session in __init__

# Import the dependency provider from main or a central dependencies file
from app.core.dependencies import get_user_service


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, 
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service) 
):
    """
    Create a new user.
    """
    # The service method already handles username/email conflict checks
    db_user = await user_service.create_user(db=db, user_in=user_in) # UserService methods take db session
    return db_user


@router.post("/login", response_model=Token)
async def login_for_access_token(
    credentials: UserLogin = Body(None), 
    form_data: OAuth2PasswordRequestForm = Depends(None),
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """
    Login endpoint that accepts both JSON credentials and form data.
    """
    # If JSON credentials are provided, use those
    if credentials:
        user_login_data = credentials
    # Otherwise, use form data
    elif form_data:
        user_login_data = UserLogin(username=form_data.username, password=form_data.password)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No credentials provided"
        )
    token = await user_service.login_user(db=db, login_data=user_login_data)
    return token

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get current logged-in user.
    """
    return current_user


@router.get("/test-auth")
async def test_auth(
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Test endpoint to verify authentication is working.
    """
    return {"message": "Authentication successful", "username": current_user.username}

# TODO: Add endpoints for:
# - Password recovery request
# - Password reset confirmation
# - Email verification (if is_active is False by default)
# - User profile update (e.g., change password, update full_name)
