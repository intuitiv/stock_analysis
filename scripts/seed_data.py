#!/usr/bin/env python3
"""
Seed script for populating initial data in the database.
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables from .env file
# This will load variables from a .env file in the project root
# It will not override existing environment variables
load_dotenv(project_root / ".env")

# Set defaults for required environment variables if not set by .env or shell
os.environ.setdefault("DATABASE_URL", "sqlite:///./naetra.db")
os.environ.setdefault("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///./naetra.db")
os.environ.setdefault("SECRET_KEY", "your-super-secret-key-here-at-least-32-chars")

from sqlalchemy import select
from app.core.database import async_session_maker, async_engine, Base
from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models import User, Stock  # Only import what we need

# ANSI color codes
BLUE = "\033[94m"     # Info
YELLOW = "\033[93m"   # Debug
RED = "\033[91m"      # Error
RESET = "\033[0m"     # Reset color

def info(msg: str) -> None:
    """Print info message in blue"""
    print(f"{BLUE}[INFO] {msg}{RESET}")

def debug(msg: str) -> None:
    """Print debug message in yellow"""
    print(f"{YELLOW}[DEBUG] {msg}{RESET}")

def error(msg: str) -> None:
    """Print error message in red"""
    print(f"{RED}[ERROR] {msg}{RESET}")

async def seed_data():
    """Populate database with initial data"""
    settings = get_settings() # Now settings will be loaded correctly
    
    debug("Initializing database schema...")
    try:
        # Create tables if they don't exist
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        info("Database schema initialized successfully.")
    except Exception as e:
        error(f"Error initializing database schema: {str(e)}")
        raise
    
    async with async_session_maker() as db:
        try:
            # Create admin user
            debug("Creating admin user...")
            admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")  # Default password, should be changed in production
            
            # Check if admin user already exists
            stmt = select(User).where(
                (User.email == admin_email) | (User.username == admin_username)
            )
            result = await db.execute(stmt)
            existing_admin = result.scalar_one_or_none()

            if not existing_admin:
                admin = User(
                    username=admin_username,
                    email=admin_email,
                    hashed_password=get_password_hash(admin_password),
                    is_active=True,
                    is_superuser=True
                )
                db.add(admin)
                await db.flush() # Ensure admin user is created before proceeding
                info(f"Admin user '{admin_username}' created successfully with email: {admin_email}")
            else:
                debug(f"Admin user '{admin_username}' or email '{admin_email}' already exists. Skipping creation.")

            # Seed stock data
            debug("Seeding stock data...")
            stock_data = [
                Stock(
                    symbol="AAPL",
                    name="Apple Inc.",
                    sector="Technology",
                    is_active=True,
                    currency="USD"
                ),
                Stock(
                    symbol="MSFT",
                    name="Microsoft Corporation.",
                    sector="Technology",
                    is_active=True,
                    currency="USD"
                ),
                Stock(
                    symbol="GOOGL",
                    name="Alphabet Inc.",
                    sector="Technology",
                    is_active=True,
                    currency="USD"
                ),
                Stock(
                    symbol="AMZN",
                    name="Amazon.com Inc.",
                    sector="Consumer Cyclical",
                    is_active=True,
                    currency="USD"
                ),
                Stock(
                    symbol="TSLA",
                    name="Tesla Inc.",
                    sector="Automotive",
                    is_active=True,
                    currency="USD"
                ),
            ]

            for stock_info in stock_data:
                # Check if stock already exists
                stmt = select(Stock).where(Stock.symbol == stock_info.symbol)
                result = await db.execute(stmt)
                existing_stock = result.scalar_one_or_none()

                if not existing_stock:
                    db.add(stock_info)
                    debug(f"Added stock: {stock_info.symbol}")
                else:
                    debug(f"Stock {stock_info.symbol} already exists. Skipping.")

            debug("Committing changes...")
            await db.commit()
            info("Data seeding completed successfully!")
            
        except Exception as e:
            await db.rollback()
            error(f"Error seeding data: {e}")
            raise

if __name__ == "__main__":
    try:
        # Add breakpoint here to debug initialization
        asyncio.run(seed_data())
    except KeyboardInterrupt:
        error("\nSeeding interrupted by user")
    except Exception as e:
        error(f"Error: {e}")
        import traceback
        traceback.print_exc()  # Print full stack trace for debugging
        sys.exit(1)
