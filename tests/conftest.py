"""
PyTest configuration and shared fixtures.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.cache import cache
from app.chaetra.brain import CHAETRA as Brain
from app.chaetra.interfaces import Evidence

settings = get_settings()

# Use test database and Redis
TEST_DATABASE_URL = "postgresql+asyncpg://localhost/test_naetra_db"
TEST_REDIS_URL = "redis://localhost:6379/1"  # Use DB 1 for testing

# Override settings for testing
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["REDIS_URL"] = TEST_REDIS_URL
os.environ["ENVIRONMENT"] = "test"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_database() -> AsyncGenerator:
    """Set up test database before each test"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Database session fixture"""
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@pytest.fixture(autouse=True)
async def override_get_db(db_session: AsyncSession) -> AsyncGenerator:
    """Override database dependency"""
    async def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    
    # Replace the dependency
    get_db.__wrapped__ = _get_test_db
    yield
    # Restore original
    get_db.__wrapped__ = get_db.__original_wrapped__

@pytest.fixture(autouse=True)
async def clean_redis() -> AsyncGenerator:
    """Clean Redis before each test"""
    await cache.clear()
    yield
    await cache.clear()

@pytest.fixture
def sample_evidence() -> Evidence:
    """Create sample evidence for testing"""
    return Evidence(
        source="test",
        content={"test": "data"},
        confidence=0.8,
        timestamp=datetime.utcnow()
    )

@pytest.fixture
def sample_market_data() -> dict:
    """Create sample market data for testing"""
    return {
        "symbol": "TEST",
        "timestamp": datetime.utcnow().isoformat(),
        "price": 100.0,
        "volume": 1000000,
        "indicators": {
            "rsi": 50,
            "macd": {"value": 0.5, "signal": 0.3}
        }
    }

@pytest.fixture
async def test_brain() -> AsyncGenerator[CHAETRABrain, None]:
    """Create test instance of CHAETRA brain"""
    brain = CHAETRABrain()
    await brain.initialize()
    yield brain
    await brain.shutdown()

# Configure pytest
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Skip slow tests unless explicitly requested
    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run slow tests"
    )

# Helper functions for tests
async def create_test_data(db_session: AsyncSession) -> None:
    """Create test data in database"""
    # Add implementation as needed for specific tests
    pass

async def clear_test_data(db_session: AsyncSession) -> None:
    """Clear test data from database"""
    # Add implementation as needed for specific tests
    pass

# Example test data generators
def generate_market_data(symbol: str = "TEST") -> dict:
    """Generate test market data"""
    return {
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "price": 100.0,
            "volume": 1000000,
            "indicators": {
                "rsi": 50,
                "macd": {
                    "value": 0.5,
                    "signal": 0.3,
                    "histogram": 0.2
                }
            }
        }
    }

def generate_evidence(
    source: str = "test",
    confidence: float = 0.8,
    content: dict = None
) -> Evidence:
    """Generate test evidence"""
    return Evidence(
        source=source,
        content=content or {"test": "data"},
        confidence=confidence,
        timestamp=datetime.utcnow()
    )
