"""Authentication schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    """User login schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    grant_type: str

class Token(BaseModel):
    """Token schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Token data schema."""
    username: str
    exp: Optional[datetime] = None

class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
