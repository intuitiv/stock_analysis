"""
NAETRA Core Package

Core components and utilities for the NAETRA application:
- Configuration management
- Database setup and connections
- Security and authentication
- Logging and caching
- Base models and shared utilities
"""

from .config import settings
from .database import (
    Base,
    get_db,
    init_db,
    async_session_maker,
    get_async_session
)
from .security import (
    create_access_token,
    verify_access_token,
    get_password_hash,
    verify_password,
    oauth2_scheme
)
from .logging import setup_logging, get_logger
from .cache import RedisCache # get_redis_client is not defined in cache.py
from .models import TimestampMixin, UUIDMixin # BaseModel is not defined in app/core/models.py

__all__ = [
    # Configuration
    'settings',
    
    # Database
    'Base',
    'get_db',
    'init_db',
    'async_session_maker',
    'get_async_session',
    
    # Security
    'create_access_token',
    'verify_access_token',
    'get_password_hash',
    'verify_password',
    'oauth2_scheme',
    
    # Logging
    'setup_logging',
    'get_logger',
    
    # Caching
    # 'get_redis_client', # Removed as it's not defined in cache.py
    'RedisCache',
    
    # Base Models
    # 'BaseModel', # Removed as it's not defined in app/core/models.py; use app.core.database.Base for SQLAlchemy
    'TimestampMixin',
    'UUIDMixin',
]
