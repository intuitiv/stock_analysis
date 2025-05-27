"""DateTime encoding utilities for consistent datetime handling."""
from datetime import datetime
from typing import Any

def format_datetime(dt: datetime) -> str:
    """Convert datetime to ISO format string."""
    return dt.isoformat() if isinstance(dt, datetime) else str(dt)

def safe_datetime_to_string(value: Any) -> Any:
    """Safely convert any datetime values to ISO format strings."""
    if isinstance(value, datetime):
        return format_datetime(value)
    elif isinstance(value, dict):
        return {k: safe_datetime_to_string(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [safe_datetime_to_string(item) for item in value]
    return value
