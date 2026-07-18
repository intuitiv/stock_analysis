"""Test database configuration."""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.config import settings

# Test database URL - using test database
TEST_DATABASE_URL = settings.database_url.replace(
    "stockanalysis", "stockanalysis_test"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=settings.db_echo_log,
    future=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow
)

# Create test session maker
test_async_session = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=settings.db_echo_log,
        future=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow
    )
    
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with test_async_session() as session:
            yield session
    finally:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def clean_db(test_db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Ensure clean database state for tests."""
    try:
        yield test_db_session
    finally:
        # Clean up tables after test
        try:
            for table in reversed(Base.metadata.sorted_tables):
                await test_db_session.execute(table.delete())
            await test_db_session.commit()
        except Exception:
            await test_db_session.rollback()
            raise
