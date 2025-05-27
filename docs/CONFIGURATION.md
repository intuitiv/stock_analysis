# NAETRA Configuration Guide

This document explains how to configure the NAETRA application for different environments and use cases.

## Environment Variables

The application uses environment variables for configuration. Copy `.env.example` to `.env` and adjust the values:

```bash
cp .env.example .env
```

### Database Configuration

NAETRA supports both SQLite and PostgreSQL databases:

#### SQLite (Development Default)
```env
DATABASE_URL=sqlite+aiosqlite:///naetra.db
```
- Simple setup, no additional configuration needed
- Good for development and testing
- No connection pooling support

#### PostgreSQL (Recommended for Production)
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/naetra
DB_ECHO=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```
- Supports connection pooling
- Better performance and concurrency
- Required for production use

### Caching Configuration

Redis is used for caching and session management:

```env
REDIS_URL=redis://localhost:6379/0
```

### Security Settings

```env
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days
```

- `SECRET_KEY`: Used for JWT token generation
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token validity period

### Market Data API Keys

```env
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
FINNHUB_API_KEY=your-finnhub-key
```

Register at:
- [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- [Finnhub](https://finnhub.io/register)

### Machine Learning Settings

```env
MODEL_CACHE_TTL=3600  # 1 hour
```

Configures how long ML model predictions are cached.

### Development Settings

```env
DEBUG=true
RELOAD=true
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Configuration Files

### alembic.ini
- Database migration configuration
- Uses the same DATABASE_URL from environment

### pytest.ini
- Test configuration
- Uses SQLite by default for testing

## Application Paths

The application uses several predefined paths:

```python
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = BASE_DIR / "app"
MODEL_DIR = APP_DIR / "models"
```

## Deployment Considerations

1. Generate a strong SECRET_KEY for production:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. Use PostgreSQL for production:
   - Create database and user
   - Update DATABASE_URL
   - Configure pool settings

3. Configure Redis:
   - Enable persistence if needed
   - Set password in production
   - Update REDIS_URL

4. Secure API keys:
   - Use environment variables
   - Never commit keys to version control
   - Rotate keys periodically

## Configuration Hierarchy

1. Environment variables
2. .env file
3. Default values in Settings class

## Validation

Configuration is validated using Pydantic:
- Type checking
- URL format validation
- Required fields enforcement
