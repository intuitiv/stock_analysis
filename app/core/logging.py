"""Logging utilities."""
import logging
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, log_dir: Path = Path("logs")) -> logging.Logger:
    """Setup logger with file handlers."""
    logger = logging.getLogger(name)
    
    # Create logs directory if it doesn't exist
    log_dir.mkdir(exist_ok=True)
    
    # Create handlers
    debug_file = log_dir / f"{name}.debug.log"
    debug_handler = logging.FileHandler(debug_file)
    debug_handler.setLevel(logging.DEBUG)
    
    info_file = log_dir / f"{name}.info.log"
    info_handler = logging.FileHandler(info_file)
    info_handler.setLevel(logging.INFO)
    
    error_file = log_dir / f"{name}.error.log"
    error_handler = logging.FileHandler(error_file)
    error_handler.setLevel(logging.ERROR)
    
    # Custom formatter with timestamp and level
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    for handler in [debug_handler, info_handler, error_handler]:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
