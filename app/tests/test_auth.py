"""Authentication tests."""
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth_schemas import UserCreate, UserUpdate

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, test_db: AsyncSession):
    """Test user creation."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = await client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert data["is_active"] is True

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient, test_db: AsyncSession, test_user: User):
    """Test user login."""
    login_data = {
        "username": test_user.username,
        "password": "testpassword123"  # From conftest.py test_user fixture
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_profile(
    client: AsyncClient,
    test_db: AsyncSession,
    test_user: User,
    test_auth_headers: dict
):
    """Test get user profile."""
    response = await client.get(
        "/api/v1/auth/profile",
        headers=test_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email

@pytest.mark.asyncio
async def test_update_profile(
    client: AsyncClient,
    test_db: AsyncSession,
    test_user: User,
    test_auth_headers: dict
):
    """Test update user profile."""
    update_data = {
        "email": "newemail@example.com"
    }
    response = await client.put(
        "/api/v1/auth/profile",
        headers=test_auth_headers,
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]

@pytest.mark.asyncio
async def test_delete_profile(
    client: AsyncClient,
    test_db: AsyncSession,
    test_user: User,
    test_auth_headers: dict
):
    """Test delete user profile."""
    response = await client.delete(
        "/api/v1/auth/profile",
        headers=test_auth_headers
    )
    assert response.status_code == 204

    # Verify user is deleted
    stmt = select(User).where(User.id == test_user.id)
    result = await test_db.execute(stmt)
    user = result.scalar_one_or_none()
    assert user is None

@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient, test_db: AsyncSession):
    """Test login with invalid credentials."""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_duplicate_username(client: AsyncClient, test_db: AsyncSession, test_user: User):
    """Test creating user with duplicate username."""
    user_data = {
        "username": test_user.username,
        "email": "another@example.com",
        "password": "testpassword123"
    }
    response = await client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_duplicate_email(client: AsyncClient, test_db: AsyncSession, test_user: User):
    """Test creating user with duplicate email."""
    user_data = {
        "username": "another_user",
        "email": test_user.email,
        "password": "testpassword123"
    }
    response = await client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == 400
