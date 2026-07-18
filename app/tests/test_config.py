"""Tests for configuration management."""
import os
from unittest import mock

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings

def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()
    assert settings.project_name == "CHAETRA Trading Assistant"
    assert settings.debug is False
    assert settings.api_prefix == "/api/v1"
    assert settings.api_v1_prefix == "/api/v1"

def test_settings_environment_override():
    """Test settings override from environment."""
    with mock.patch.dict(os.environ, {
        "PROJECT_NAME": "Test App",
        "DEBUG": "true",
        "API_PREFIX": "/test",
        "API_V1_PREFIX": "/test/v1"
    }):
        settings = Settings()
        assert settings.project_name == "Test App"
        assert settings.debug is True
        assert settings.api_prefix == "/test"
        assert settings.api_v1_prefix == "/test/v1"

def test_settings_validation():
    """Test settings validation."""
    with mock.patch.dict(os.environ, {
        "MARKET_DATA_PROVIDER": "invalid_provider",
        "LLM_PROVIDER": "invalid_provider"
    }):
        settings = Settings()
        # Should fall back to mock for invalid providers
        assert settings.market_data_provider == "mock"
        assert settings.llm_provider == "mock"

def test_required_settings():
    """Test required settings validation."""
    with pytest.raises(ValidationError):
        # Should fail without required SECRET_KEY
        Settings(database_url="postgresql://localhost/test")

def test_get_settings_cache():
    """Test settings caching."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2  # Should be the same instance

def test_database_url_validation():
    """Test database URL validation."""
    with pytest.raises(ValidationError):
        Settings(
            secret_key="test",
            database_url="invalid://url"  # Invalid URL pattern
        )

    # Valid PostgreSQL URL should work
    settings = Settings(
        secret_key="test",
        database_url="postgresql://user:pass@localhost/db"
    )
    assert settings.database_url == "postgresql://user:pass@localhost/db"
