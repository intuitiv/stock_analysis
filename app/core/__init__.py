"""Core module initialization."""
from typing import TYPE_CHECKING

from .database import Base, async_engine, async_session_maker, get_db

def _load_settings():
    from .config import settings
    return settings

def _load_security():
    from .security import (
        get_password_hash,
        verify_password,
        create_access_token,
        verify_access_token,
        get_current_user
    )
    return (
        get_password_hash,
        verify_password,
        create_access_token,
        verify_access_token,
        get_current_user
    )

if TYPE_CHECKING:
    from typing import Callable
    from fastapi import Depends
    from app.models.user import User
    from .config import Settings

    def get_password_hash(password: str) -> str: ...
    def verify_password(plain_password: str, hashed_password: str) -> bool: ...
    def create_access_token(data: dict) -> str: ...
    def verify_access_token(token: str) -> dict: ...
    def get_current_user(token: str = Depends()) -> User: ...
    settings: Settings
else:
    settings = _load_settings()
    (
        get_password_hash,
        verify_password,
        create_access_token,
        verify_access_token,
        get_current_user
    ) = _load_security()

__all__ = [
    'settings',
    'Base',
    'async_engine',
    'async_session_maker',
    'get_db',
    'get_password_hash',
    'verify_password',
    'create_access_token', 
    'verify_access_token',
    'get_current_user'
]
