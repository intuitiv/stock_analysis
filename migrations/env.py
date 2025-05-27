"""
Migration environment configuration
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import the settings and Base from app
from app.core.config import settings
from app.core.database import Base

# Include all models to detect for migrations
from app.models import *  # noqa

# Import or define your model's MetaData object here
target_metadata = Base.metadata

# Read alembic.ini config
config = context.config

# Optional logging configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url():
    """Get database URL from settings"""
    return str(settings.ASYNC_DATABASE_URL)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    async with async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        url=lambda: get_url(),
    ) as engine:

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await context.run_migrations()
