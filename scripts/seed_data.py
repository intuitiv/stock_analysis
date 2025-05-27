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
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/stockanalysis_dev")
os.environ.setdefault("ASYNC_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/stockanalysis_dev")
os.environ.setdefault("SECRET_KEY", "your-super-secret-key-here-at-least-32-chars")

from sqlalchemy import select
from app.core.database import async_session_maker, async_engine, Base
from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models import (
    User, Stock, Portfolio, Position, Transaction, TransactionType,
    Analysis, AnalysisType, AnalysisStatus, AnalysisInput, AnalysisResult, AnalysisRun,
    ChatSession, ChatMessage, MessageRole
)

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

async def create_database():
    """Create the database if it doesn't exist."""
    try:
        import asyncpg
        # Connect to default postgres database to create new database
        conn = await asyncpg.connect(
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432',
            database='postgres'
        )

        # Check if database exists
        result = await conn.fetchrow(
            "SELECT 1 FROM pg_database WHERE datname=$1",
            'stockanalysis_dev'
        )
        
        if result is None:
            # Close other connections to the template database
            await conn.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'stockanalysis_dev'
                AND pid <> pg_backend_pid()
            """)
            # Create database
            await conn.execute("CREATE DATABASE stockanalysis_dev")
            info("Database 'stockanalysis_dev' created successfully.")
        else:
            debug("Database 'stockanalysis_dev' already exists.")
        
        await conn.close()
    except Exception as e:
        error(f"Error creating database: {str(e)}")
        raise

async def seed_data():
    """Populate database with initial data"""
    settings = get_settings() # Now settings will be loaded correctly
    
    # Create database if it doesn't exist
    debug("Checking database...")
    await create_database()
    
    debug("Dropping all tables...")
    try:
        # Drop all tables first
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        info("All tables dropped successfully.")
        
        debug("Creating new tables...")
        # Create tables fresh
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

            # Create default portfolio for admin
            debug("Creating default portfolio for admin...")
            default_portfolio = Portfolio(
                user_id=admin.id,
                name="Default Portfolio",
                description="Default portfolio created during setup",
                currency="USD"
            )
            db.add(default_portfolio)
            await db.flush()
            
            # Create sample analysis
            debug("Creating sample analysis...")
            sample_analysis = Analysis(
                name="Daily AAPL Technical Analysis",
                description="Daily technical analysis of Apple stock",
                analysis_type=AnalysisType.TECHNICAL,
                user_id=admin.id,
                is_active=True,
                configuration={"indicators": ["SMA", "RSI", "MACD"]}
            )
            db.add(sample_analysis)
            await db.flush()

            # Create sample analysis run
            analysis_run = AnalysisRun(
                analysis_id=sample_analysis.id,
                status=AnalysisStatus.COMPLETED,
                execution_metadata={"execution_time": "2.5s"}
            )
            db.add(analysis_run)
            await db.flush()

            # Create sample analysis result
            analysis_result = AnalysisResult(
                analysis_run_id=analysis_run.id,
                result_type="technical_indicators",
                result_data={
                    "sma": 150.25,
                    "rsi": 65.5,
                    "macd": {"line": 2.5, "signal": 1.8, "histogram": 0.7}
                },
                confidence_score=0.85
            )
            db.add(analysis_result)

            # Create sample analysis input
            analysis_input = AnalysisInput(
                analysis_id=sample_analysis.id,
                parameter_name="period",
                parameter_value={"days": 14},
                parameter_type="integer"
            )
            db.add(analysis_input)

            # Create sample position for AAPL
            aapl_stock = await db.execute(select(Stock).where(Stock.symbol == "AAPL"))
            aapl_stock = aapl_stock.scalar_one()
            
            position = Position(
                portfolio_id=default_portfolio.id,
                stock_id=aapl_stock.id,
                quantity=100,
                average_price=150.0
            )
            db.add(position)
            await db.flush()

            # Create sample transaction
            transaction = Transaction(
                portfolio_id=default_portfolio.id,
                position_id=position.id,
                stock_id=aapl_stock.id,
                transaction_type=TransactionType.BUY,
                quantity=100,
                price=150.0,
                fees=7.99,
                notes="Initial purchase of AAPL stock"
            )
            db.add(transaction)

            # Create sample chat session
            chat_session = ChatSession(
                user_id=admin.id,
                title="Stock Analysis Discussion",
                context={"analysis_id": sample_analysis.id},
                is_active=True,
                session_metadata={"source": "web"}
            )
            db.add(chat_session)
            await db.flush()

            # Create sample chat messages
            messages = [
                ChatMessage(
                    session_id=chat_session.id,
                    role=MessageRole.USER,
                    content="Can you analyze AAPL's performance?",
                    message_metadata={"timestamp": "2025-05-23T12:00:00Z"}
                ),
                ChatMessage(
                    session_id=chat_session.id,
                    role=MessageRole.ASSISTANT,
                    content="Based on the technical analysis, AAPL shows a bullish trend with RSI at 65.5.",
                    message_metadata={"timestamp": "2025-05-23T12:00:01Z"},
                    analysis_id=sample_analysis.id,
                    analysis_result_id=analysis_result.id
                )
            ]
            for message in messages:
                db.add(message)

            debug("Committing changes...")
            await db.commit()
            info("Data seeding completed successfully!")
            
        except Exception as e:
            await db.rollback()
            error(f"Error seeding data: {e}")
            raise

if __name__ == "__main__":
    try:
        # Import create_engine here to avoid circular imports
        from sqlalchemy import create_engine
        # Add breakpoint here to debug initialization
        asyncio.run(seed_data())
    except KeyboardInterrupt:
        error("\nSeeding interrupted by user")
    except Exception as e:
        error(f"Error: {e}")
        import traceback
        traceback.print_exc()  # Print full stack trace for debugging
        sys.exit(1)
