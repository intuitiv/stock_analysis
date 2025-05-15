"""
Logging configuration for the NAETRA application.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.config import settings

# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Create a null handler for SQLAlchemy
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application-wide logging.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Completely disable SQLAlchemy logging
    sqlalchemy_loggers = [
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "sqlalchemy.orm"
    ]
    
    for logger_name in sqlalchemy_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(NullHandler())
        logger.propagate = False
        logger.setLevel(logging.CRITICAL)  # Only show critical errors

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Add our handlers
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    file_handler = RotatingFileHandler(
        LOGS_DIR / "naetra_app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set other loggers to appropriate levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    """
    logger = logging.getLogger(name)
    # Ensure SQLAlchemy loggers don't propagate
    if name.startswith("sqlalchemy."):
        logger.propagate = False
        logger.addHandler(NullHandler())
    return logger

# Force disable SQLAlchemy logging right away
for logger_name in ["sqlalchemy.engine", "sqlalchemy.pool", "sqlalchemy.dialects", "sqlalchemy.orm"]:
    logger = logging.getLogger(logger_name)
    logger.addHandler(NullHandler())
    logger.propagate = False
    logger.setLevel(logging.CRITICAL)

# Initialize logging when this module is imported
if __name__ != "__main__": # Avoid running setup if module is run directly
    setup_logging(log_level="DEBUG" if settings.DEBUG else "INFO")

# Example usage:
# from app.core.logging import get_logger
# logger = get_logger(__name__)
# logger.info("This is an info message.")
# logger.error("This is an error message.")
