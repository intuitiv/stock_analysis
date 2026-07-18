from datetime import timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status

from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.models.user import User as UserModel # SQLAlchemy model
from app.schemas.auth_schemas import UserCreate, UserResponse, UserLogin, Token
from app.core.database import get_db # Assuming a session factory

class UserService:
    # If not using FastAPI's Depends for the service itself,
    # db_session_factory can be passed to __init__
    # def __init__(self, db_session_factory: Callable[[], ContextManager[Session]]):
    #     self.db_session_factory = db_session_factory

    async def get_user_by_username(self, db: Session, username: str) -> Optional[UserModel]:
        return db.query(UserModel).filter(UserModel.username == username).first()

    async def get_user_by_email(self, db: Session, email: str) -> Optional[UserModel]:
        return db.query(UserModel).filter(UserModel.email == email).first()

    async def get_user_by_id(self, db: Session, user_id: int) -> Optional[UserModel]:
        return db.query(UserModel).filter(UserModel.id == user_id).first()

    async def create_user(self, db: Session, user_in: UserCreate) -> UserModel:
        if await self.get_user_by_username(db, user_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        if await self.get_user_by_email(db, user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        hashed_password = get_password_hash(user_in.password)
        db_user = UserModel(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            is_active=True, # Or require email verification
            is_superuser=False # Default to not superuser
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    async def authenticate_user(self, db: Session, login_data: UserLogin) -> Optional[UserModel]:
        # Allow login with username or email
        user = await self.get_user_by_username(db, login_data.username)
        if not user:
            user = await self.get_user_by_email(db, login_data.username) # Try email
        
        if not user:
            return None # User not found
        if not verify_password(login_data.password, user.hashed_password):
            return None # Incorrect password
        
        return user

    async def login_user(self, db: Session, login_data: UserLogin) -> Token:
        user = await self.authenticate_user(db, login_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}, # Include user_id in token
            expires_delta=access_token_expires
        )
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def update_user(self, db: Session, user_id: int, updates: Dict[str, Any]) -> Optional[UserModel]:
        db_user = await self.get_user_by_id(db, user_id)
        if not db_user:
            return None
        
        for key, value in updates.items():
            if hasattr(db_user, key) and value is not None:
                if key == "password": # Handle password update separately
                    setattr(db_user, "hashed_password", get_password_hash(value))
                else:
                    setattr(db_user, key, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user

    # Placeholder for password reset logic
    # async def request_password_reset(self, db: Session, email: str) -> bool: ...
    # async def reset_password(self, db: Session, token: str, new_password: str) -> bool: ...

    # Static method for dependency injection if preferred over instance-based DI
    # @staticmethod
    # def get_instance(db: Session = Depends(get_db_session)): # Assuming get_db_session provides a session
    #     return UserService(db_session_factory=lambda: db) # This is a bit tricky for non-request scope
    # A simpler way for FastAPI is to just Depends(UserService) if __init__ takes Depends(get_db)

# To use with FastAPI Depends:
# class UserService:
#     def __init__(self, db: Session = Depends(get_db_session)):
#         self.db = db
#     async def get_user_by_username(self, username: str) -> Optional[UserModel]:
#        return self.db.query(UserModel).filter(UserModel.username == username).first()
#     ... etc ...
# Then in routes: user_svc: UserService = Depends(UserService)
# The current structure assumes db session is passed to each method,
# which is also a common pattern if the service methods are called from places
# where a session is already available (like within a request that has `db: Session = Depends(get_db)`).
