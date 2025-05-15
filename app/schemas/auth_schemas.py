"""
Authentication and user-related Pydantic schemas.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator

class Token(BaseModel):
    """Access token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int # Consider making this optional or deriving from settings

class TokenData(BaseModel):
    """Token payload schema."""
    username: Optional[str] = None
    user_id: Optional[int] = None # Added user_id for convenience
    exp: Optional[datetime] = None

class UserBase(BaseModel):
    """Base user schema with shared attributes."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$") # Added pattern
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        """Ensure password meets complexity requirements."""
        # Example: At least one uppercase, one lowercase, one digit.
        # Adjust complexity as needed.
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        # if not any(c in "!@#$%^&*()_+-=[]{};':\"\\|,.<>/?`~" for c in v):
        #     raise ValueError('Password must contain at least one special character')
        return v

class UserUpdate(UserBase):
    """Schema for updating user information."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: Optional[str] = Field(None, min_length=8)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    
    @validator('password')
    def validate_password_optional(cls, v): # Renamed to avoid conflict if UserBase had this
        """Validate password if provided."""
        if v is None:
            return v
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class UserInDB(UserBase):
    """User schema as stored in database."""
    id: int
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False # Added superuser field
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Changed from orm_mode for Pydantic v2

class UserResponse(UserBase):
    """User schema for API responses."""
    id: int
    is_active: bool
    is_superuser: bool # Added superuser field
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Changed from orm_mode for Pydantic v2

class UserLogin(BaseModel): # Definition for UserLogin
    """Schema for user login."""
    username: str # Can be username or email
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_new_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v
