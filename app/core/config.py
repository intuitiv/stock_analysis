"""
Configuration settings for NAETRA application.
Uses pydantic-settings for environment variable validation.
"""
import json # Added for parsing JSON strings from .env
from typing import Any, Dict, Optional, List, Tuple # Added Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import RedisDsn, SecretStr, field_validator, AnyUrl, ConfigDict


class Settings(BaseSettings):
    # Application - These have defaults but can be overridden
    APP_NAME: str = "NAETRA" # Default, can be overridden
    APP_VERSION: str = "0.1.0" # Default, can be overridden
    DEBUG: bool = False # Default, can be overridden
    API_V1_PREFIX: str = "/api/v1" # Default, can be overridden

    LOG_LEVEL: str = "DEBUG" # Default, can be overridden
    LOG_FORMAT: str = '%(levelname)s:     %(asctime)s %(name)s - %(message)s' # Default, can be overridden

    # Security
    SECRET_KEY: SecretStr # Critical, must be in .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Default, can be overridden
    ALGORITHM: str = "HS256" # Default, can be overridden

    # Database
    DATABASE_URL: str # Critical, must be in .env
    ASYNC_DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL scheme."""
        allowed_schemes = [
            "sqlite", "sqlite+aiosqlite",
            "postgresql", "postgresql+asyncpg",
            "postgresql+psycopg"
        ]
        scheme = v.split("://")[0]
        if scheme not in allowed_schemes:
            raise ValueError(f"Invalid database scheme. Must be one of: {allowed_schemes}")
        return v

    DB_ECHO_LOG: bool = False # Default, can be overridden
    DB_POOL_SIZE: int = 5 # Default, can be overridden
    DB_MAX_OVERFLOW: int = 10 # Default, can be overridden

    # Redis
    REDIS_URL: Optional[RedisDsn] = None # Default (None means optional), can be overridden
    REDIS_POOL_SIZE: int = 10 # Default, can be overridden

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"] # Default, can be overridden (JSON string in .env)
    CORS_ALLOW_CREDENTIALS: bool = True # Default, can be overridden

    @field_validator("ALLOWED_ORIGINS", mode='before')
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                loaded_v = json.loads(v)
                if not isinstance(loaded_v, list) or not all(isinstance(item, str) for item in loaded_v):
                    raise ValueError("ALLOWED_ORIGINS must be a list of strings when parsed from JSON.")
                return loaded_v
            except json.JSONDecodeError:
                # If not valid JSON, assume it's a comma-separated string
                return [origin.strip() for origin in v.split(',')]
        elif isinstance(v, list) and all(isinstance(item, str) for item in v):
            return v # Already a list of strings (e.g. from default value)
        raise ValueError("ALLOWED_ORIGINS must be a list of strings or a comma-separated string or a JSON string list.")

    # Market Data Provider Settings
    YAHOO_FINANCE_ENABLED: bool = True # Default, can be overridden
    ALPHA_VANTAGE_ENABLED: bool = True # Default, can be overridden
    FINNHUB_ENABLED: bool = False # Default, can be overridden. Set to True to use Finnhub.
    MARKET_DATA_PROVIDER: str = "yahoo_finance"  # Default, can be overridden (e.g., "finnhub", "alpha_vantage")
    DEFAULT_HISTORICAL_DATA_PERIOD_DAYS: int = 365 # Default, can be overridden
    MARKET_OVERVIEW_INDICES: List[str] = ["^GSPC", "^IXIC", "^DJI"]  # Default, can be overridden (JSON string in .env)
    INDEX_NAMES: Dict[str, str] = { # Default, can be overridden (JSON string in .env)
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "^DJI": "Dow Jones"
    }
    MARKET_DATA_CACHE_TTL_SECONDS: int = 300 # Default, can be overridden

    @field_validator("MARKET_OVERVIEW_INDICES", mode='before')
    @classmethod
    def parse_market_overview_indices(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("INDEX_NAMES", mode='before')
    @classmethod
    def parse_index_names(cls, v: Any) -> Dict[str, str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    # CHAETRA Engine Settings - All have defaults, can be overridden
    # Learning System Settings
    CHAETRA_LEARNING_MIN_PATTERN_CONFIDENCE: float = 0.6
    CHAETRA_LEARNING_MIN_VALIDATIONS_FOR_CORE: int = 3
    CHAETRA_LEARNING_SUCCESS_THRESHOLD_PERCENT: float = 1.0
    
    # Technical Analysis Settings (related to Chaetra, distinct from general TA settings below)
    CHAETRA_TREND_SMA_SHORT_PERIOD: int = 10
    CHAETRA_TREND_SMA_LONG_PERIOD: int = 50
    
    # Memory System Settings
    CHAETRA_MEMORY_VALIDATION_THRESHOLD: int = 3
    CHAETRA_MEMORY_CORE_CONFIDENCE_THRESHOLD: float = 0.8
    CHAETRA_MEMORY_SHORT_TERM_TTL_SECONDS: int = 86400  # 24 hours
    CHAETRA_MEMORY_VALIDATION_CONFIDENCE_BOOST: float = 0.1
    CHAETRA_MEMORY_ARCHIVE_CONFIDENCE_THRESHOLD: float = 0.3
    
    # Sentiment Analysis Settings
    SENTIMENT_POSITIVE_THRESHOLD: float = 0.15
    SENTIMENT_NEGATIVE_THRESHOLD: float = -0.15
    
    # Fundamental Analysis Settings
    FUNDAMENTAL_ANALYSIS_DEFAULT_PERIODS: int = 4
    
    # Reasoning System Settings
    CHAETRA_REASONING_HYPOTHESIS_CONFIDENCE: float = 0.7
    
    # Opinion System Settings
    CHAETRA_OPINION_MIN_CONFIDENCE_TO_STORE: float = 0.6

    # External APIs - Critical, must be in .env if provider is enabled
    ALPHA_VANTAGE_API_KEY: Optional[SecretStr] = None
    YAHOO_FINANCE_API_KEY: Optional[SecretStr] = None # Currently not used by yfinance library
    FINNHUB_API_KEY: Optional[SecretStr] = None # For Finnhub integration

    # LLM Provider Settings
    DEFAULT_LLM_PROVIDER: str = "gemini" # Default, can be overridden
    LLM_PROVIDER_ORDER: List[str] = ["gemini", "openai", "lm_studio", "ollama"]  # Default, can be overridden (JSON string in .env)
    LLM_PROVIDER_CACHE_TTL_SECONDS: int = 3600  # Default, can be overridden
    LLM_API_TIMEOUT_SECONDS: int = 30 # Default timeout for LLM API calls, can be overridden

    @field_validator("LLM_PROVIDER_ORDER", mode='before')
    @classmethod
    def parse_llm_provider_order(cls, v: Any) -> List[str]: # Changed name to avoid conflict
        if isinstance(v, str):
            try:
                loaded_v = json.loads(v) # Try parsing as JSON list first
                if not isinstance(loaded_v, list) or not all(isinstance(item, str) for item in loaded_v):
                     raise ValueError("LLM_PROVIDER_ORDER must be a list of strings if JSON.")
                v_list = loaded_v
            except json.JSONDecodeError:
                v_list = [p.strip().lower() for p in v.split(",")] # Fallback to comma-separated
        elif isinstance(v, list) and all(isinstance(item, str) for item in v):
            v_list = v
        else:
            raise ValueError("LLM_PROVIDER_ORDER must be a list of strings, a comma-separated string, or a JSON string list.")

        valid_providers = {"gemini", "openai", "lm_studio", "ollama"}
        for p in v_list:
            if p not in valid_providers:
                print(f"Warning: Unknown provider '{p}' in LLM_PROVIDER_ORDER. It will be ignored if not implemented.")
        return v_list

    # OpenAI Settings
    OPENAI_API_KEY: Optional[SecretStr] = None # Critical, must be in .env if openai is used
    OPENAI_MODEL: str = "gpt-3.5-turbo" # Default, can be overridden

    # Gemini Settings
    GEMINI_API_KEY: Optional[SecretStr] = None # Critical, must be in .env if gemini is used
    GEMINI_MODEL: str = "gemini-1.5-flash-latest" # Default, can be overridden

    # Ollama Settings
    OLLAMA_API_URL: Optional[str] = None # Default (None), must be set in .env if ollama is used
    OLLAMA_MODEL: Optional[str] = None # Default (None), must be set in .env if ollama is used

    # LM Studio Settings (OpenAI compatible)
    LM_STUDIO_BASE_URL: Optional[str] = None # Default (None), must be set in .env if lm_studio is used
    LM_STUDIO_MODEL: Optional[str] = None # Default (None), can be set in .env

    # SEC EDGAR Settings - All have defaults, can be overridden
    SEC_EDGAR_USER_AGENT: str = "MyStockAnalysisApp/1.0 contact@example.com"
    SEC_COMPANY_FACTS_URL: str = "https://data.sec.gov/api/xbrl/companyfacts/"
    SEC_SUBMISSIONS_URL: str = "https://data.sec.gov/submissions/"
    SEC_RATE_LIMIT_PER_SEC: int = 10

    # Technical Analysis Settings - All have defaults, can be overridden
    TECHNICAL_ANALYSIS_DEFAULT_HISTORY_DAYS: int = 365
    DEFAULT_SMA_PERIODS: List[int] = [20, 50, 200] # Default, can be overridden (JSON string in .env)
    DEFAULT_EMA_PERIODS: List[int] = [12, 26] # Default, can be overridden (JSON string in .env)
    DEFAULT_RSI_PERIOD: int = 14
    DEFAULT_MACD_PARAMS: Tuple[int, int, int] = (12, 26, 9) # Default, can be overridden (JSON string in .env)
    DEFAULT_BBANDS_PERIOD: int = 20
    DEFAULT_BBANDS_STDDEV: float = 2.0
    
    @field_validator("DEFAULT_SMA_PERIODS", "DEFAULT_EMA_PERIODS", mode='before')
    @classmethod
    def parse_list_int(cls, v: Any) -> List[int]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("DEFAULT_MACD_PARAMS", mode='before')
    @classmethod
    def parse_tuple_int(cls, v: Any) -> Tuple[int, int, int]:
        if isinstance(v, str):
            loaded_v = json.loads(v)
            if isinstance(loaded_v, list) and len(loaded_v) == 3 and all(isinstance(i, int) for i in loaded_v):
                return tuple(loaded_v)
            raise ValueError("DEFAULT_MACD_PARAMS must be a JSON list of 3 integers.")
        return v
    
    @field_validator("ASYNC_DATABASE_URL", mode='before')
    def assemble_async_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """Convert DATABASE_URL to async version if ASYNC_DATABASE_URL not provided."""
        if v is not None:
            return v

        db_url = values.get("DATABASE_URL")
        if not db_url:
            raise ValueError("Either DATABASE_URL or ASYNC_DATABASE_URL must be provided")

        db_url_str = str(db_url)
        if db_url_str.startswith('postgresql://'):
            # For PostgreSQL, use asyncpg as async driver
            return db_url_str.replace("postgresql://", "postgresql+asyncpg://")
        elif db_url_str.startswith('sqlite:///'):
            # For SQLite, use aiosqlite as async driver
            return db_url_str.replace("sqlite:///", "sqlite+aiosqlite:///")
        else:
            # Return as-is for other database types
            return db_url_str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        arbitrary_types_allowed=True,  # Allow AnyUrl and other complex types
        validate_default=True
    )


# Create global settings instance
settings = Settings()


def get_settings():
    return settings
