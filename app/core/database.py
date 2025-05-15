"""
Database configuration and session management for NAETRA.
Provides both synchronous and asynchronous database access.
"""

import os
from pathlib import Path
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Ensure database directory exists for SQLite
def prepare_sqlite_url(url: str) -> str:
    """Prepare SQLite URL by ensuring directory exists."""
    if url.startswith(('sqlite:///', 'sqlite+aiosqlite:///')):
        # Extract the database file path
        db_path = url.split('///')[-1]
        if db_path != ':memory:':
            # Create directory if it doesn't exist
            db_dir = os.path.dirname(db_path)
            if db_dir:
                Path(db_dir).mkdir(parents=True, exist_ok=True)
    return url

# Prepare database URLs
sync_db_url = prepare_sqlite_url(str(settings.DATABASE_URL))
async_db_url = prepare_sqlite_url(str(settings.ASYNC_DATABASE_URL))

# Create async engine for the PostgreSQL database
async_engine = create_async_engine(
    async_db_url,
    echo=False,  # Disable SQL logging
    echo_pool=False,  # Disable connection pool logging
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW
)

# Create sync engine for tasks that require synchronous access
sync_engine = create_engine(
    sync_db_url,
    echo=False,  # Disable SQL logging
    echo_pool=False,  # Disable connection pool logging
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW
)

# Session factories
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

# Base class for SQLAlchemy models
Base = declarative_base()

async def init_db() -> None:
    """Initialize database, creating all tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes that need async database access."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI routes that need synchronous database access."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
