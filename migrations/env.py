import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import create_engine


from alembic import context

# Import Base and models
from app.core.database import Base
# Ensure all models are imported here so Alembic can see them
# from app.core.models import BaseModel # BaseModel is not defined in app.core.models; Pydantic's BaseModel or SQLAlchemy's Base are used elsewhere.
import app.models # This will make User, Stock, Portfolio, etc. available via Base.metadata
# If you have other specific model files, import them too, e.g.:
# from app.models.market_data import MarketData
# from app.models.technical_indicators import TechnicalIndicator
# from app.models.strategy import Strategy
from app.core.config import settings # Changed from get_settings to settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
# settings instance is directly imported now. The line `settings = get_settings()` is removed.

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = settings.DATABASE_URL.replace("+asyncpg", "") # Use sync URL for offline
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # For online mode, we use the async URL from settings
    # but Alembic itself needs a sync engine for some operations.
    # We'll use the sync URL from alembic.ini for the connectable.
        
    # The connectable for run_sync should be an async engine
    # The URL for async_engine_from_config should be the ASYNC_DATABASE_URL
    # settings.DATABASE_URL might be sync or async depending on its original form.
    # settings.ASYNC_DATABASE_URL is guaranteed to be in async format.
    connectable = async_engine_from_config(
        {"sqlalchemy.url": str(settings.ASYNC_DATABASE_URL)}, # Use ASYNC_DATABASE_URL
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
