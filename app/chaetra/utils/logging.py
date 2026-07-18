"""Logging utilities for CHAETRA."""
import logging
from typing import Dict, Any, Optional
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
import os
from functools import wraps
import time
import traceback

class CHAETRALogger:
    """Custom logger for CHAETRA components."""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.logger = logging.getLogger(f"chaetra.{name}")
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, f"{name}.log"),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _format_log(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ) -> str:
        """Format log message with additional data."""
        log_entry = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if data:
            log_entry["data"] = data
            
        if error:
            log_entry["error"] = {
                "type": error.__class__.__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
            
        return json.dumps(log_entry)

    def info(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self.logger.info(self._format_log(message, data))

    def warning(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self.logger.warning(self._format_log(message, data))

    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """Log error message."""
        self.logger.error(self._format_log(message, data, error))

    def debug(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self.logger.debug(self._format_log(message, data))

def log_execution_time(logger: CHAETRALogger):
    """Decorator to log function execution time."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"{func.__name__} completed",
                    {
                        "execution_time": execution_time,
                        "success": True
                    }
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed",
                    error=e,
                    data={
                        "execution_time": execution_time,
                        "success": False
                    }
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"{func.__name__} completed",
                    {
                        "execution_time": execution_time,
                        "success": True
                    }
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed",
                    error=e,
                    data={
                        "execution_time": execution_time,
                        "success": False
                    }
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Create loggers for each component
memory_logger = CHAETRALogger("memory")
learning_logger = CHAETRALogger("learning")
reasoning_logger = CHAETRALogger("reasoning")
opinion_logger = CHAETRALogger("opinion")
llm_logger = CHAETRALogger("llm")
cache_logger = CHAETRALogger("cache")
brain_logger = CHAETRALogger("brain")
