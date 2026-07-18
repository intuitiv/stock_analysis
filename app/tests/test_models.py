"""Model tests."""
import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth_schemas import UserCreate

@pytest.mark.asyncio
async def test_create_user(test_db: AsyncSession):
    """Test user model creation."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.is_active is True

@pytest.mark.asyncio
async def test_get_user_by_username(test_db: AsyncSession):
    """Test getting user by username."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    test_db.add(user)
    await test_db.commit()

    # Test get by username
    found_user = await User.get_by_username(test_db, "testuser")
    assert found_user is not None
    assert found_user.username == "testuser"
    assert found_user.email == "test@example.com"

@pytest.mark.asyncio
async def test_get_user_by_email(test_db: AsyncSession):
    """Test getting user by email."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    test_db.add(user)
    await test_db.commit()

    # Test get by email
    found_user = await User.get_by_email(test_db, "test@example.com")
    assert found_user is not None
    assert found_user.username == "testuser"
    assert found_user.email == "test@example.com"

@pytest.mark.asyncio
async def test_user_relationships(test_db: AsyncSession):
    """Test user relationships."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    test_db.add(user)
    await test_db.commit()

    # Test relationships are initialized empty
    assert user.portfolios == []
    assert user.analyses == []
    assert user.chat_sessions == []

@pytest.mark.asyncio
async def test_user_model_str(test_db: AsyncSession):
    """Test user model string representation."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    test_db.add(user)
    await test_db.commit()

    assert str(user) == f"User(id={user.id}, username=testuser)"

@pytest.mark.asyncio
async def test_user_timestamps(test_db: AsyncSession):
    """Test user timestamp fields."""
    before_create = datetime.utcnow()
    
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    test_db.add(user)
    await test_db.commit()
    
    after_create = datetime.utcnow()

    assert before_create <= user.created_at <= after_create
    assert before_create <= user.updated_at <= after_create

    # Test update
    original_updated_at = user.updated_at
    user.email = "newemail@example.com"
    await test_db.commit()
    await test_db.refresh(user)

    assert user.updated_at > original_updated_at
    assert user.created_at == original_updated_at  # created_at shouldn't change
