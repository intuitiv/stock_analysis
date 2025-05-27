"""Test fixtures."""
import asyncio
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.security import get_password_hash
from app.models.user import User
from app.main import create_app

# Test settings
test_settings = Settings(
    database_url="sqlite+aiosqlite:///./test.db",
    database_echo=True,
    secret_key="test-secret-key",
)

# Test database engine
test_engine = create_async_engine(
    test_settings.database_url,
    echo=test_settings.database_echo
)

# Test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture
async def app() -> FastAPI:
    """Create test app."""
    return create_app()

@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_db() -> AsyncSession:
    """Create test database session."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest.fixture
async def test_auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Create test authentication headers."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user.username,
            "password": "testpassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()
