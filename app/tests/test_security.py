"""Security tests."""
import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    verify_access_token,
    get_password_hash,
    verify_password
)

def test_password_hashing():
    """Test password hashing functions."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    # Verify hash is different from original
    assert hashed != password
    
    # Verify correct password
    assert verify_password(password, hashed) is True
    
    # Verify incorrect password
    assert verify_password("wrongpassword", hashed) is False

def test_create_access_token():
    """Test access token creation."""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    # Verify token is string
    assert isinstance(token, str)
    
    # Decode and verify token
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm]
    )
    
    assert payload["sub"] == "testuser"
    assert "exp" in payload
    
    # Verify expiration
    exp = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    delta = exp - now
    
    # Should be close to the configured expiration time
    expected_delta = timedelta(minutes=settings.access_token_expire_minutes)
    assert abs(delta - expected_delta) < timedelta(seconds=10)

@pytest.mark.asyncio
async def test_verify_access_token():
    """Test access token verification."""
    # Create token
    user_data = {"sub": "testuser"}
    token = create_access_token(user_data)
    
    # Verify valid token
    payload = verify_access_token(token)
    assert payload["sub"] == "testuser"
    
    # Test invalid token
    with pytest.raises(jwt.JWTError):
        verify_access_token("invalid.token.here")
    
    # Test expired token
    expired_token = create_access_token(
        user_data,
        expires_delta=timedelta(minutes=-1)
    )
    with pytest.raises(jwt.JWTError):
        verify_access_token(expired_token)

def test_token_expiration():
    """Test token expiration times."""
    data = {"sub": "testuser"}
    
    # Test default expiration
    token = create_access_token(data)
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm]
    )
    exp = datetime.fromtimestamp(payload["exp"])
    assert exp > datetime.utcnow()
    
    # Test custom expiration
    custom_expires = timedelta(minutes=30)
    token = create_access_token(data, expires_delta=custom_expires)
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm]
    )
    exp = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    assert abs(exp - now - custom_expires) < timedelta(seconds=10)
