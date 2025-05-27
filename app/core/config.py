"""
Consolidated and Corrected Configuration for NAETRA Application.
Powered by pydantic-settings for robust environment variable management.
"""

import json
from typing import Any, Dict, Optional, List, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import RedisDsn, SecretStr, field_validator, ValidationInfo, model_validator

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "NAETRA"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Logging Configuration
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = '%(levelname)s: %(asctime)s %(name)s - %(message)s'

    # Security Settings
    SECRET_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Database Configuration
    DATABASE_URL: str
    ASYNC_DATABASE_URL: Optional[str] = None
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        allowed_schemes = [
            "sqlite", "sqlite+aiosqlite",
            "postgresql", "postgresql+asyncpg",
            "postgresql+psycopg"
        ]
        scheme = v.split("://")[0]
        if scheme not in allowed_schemes:
            raise ValueError(f"Invalid database scheme. Must be one of: {allowed_schemes}")
        return v

    @field_validator("ASYNC_DATABASE_URL", mode='before')
    def assemble_async_db_url(cls, v: Optional[str], info: ValidationInfo) -> str:
        if v is not None:
            return v
        db_url = info.data.get("DATABASE_URL")
        if not db_url:
            raise ValueError("Either DATABASE_URL or ASYNC_DATABASE_URL must be provided")
        db_url_str = str(db_url)
        if db_url_str.startswith('postgresql://'):
            return db_url_str.replace("postgresql://", "postgresql+asyncpg://")
        elif db_url_str.startswith('sqlite:///'):
            return db_url_str.replace("sqlite:///", "sqlite+aiosqlite:///")
        return db_url_str

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_DSN: Optional[RedisDsn] = None
    REDIS_POOL_SIZE: int = 10
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_DB: int = 0

    @field_validator("REDIS_URL")
    def ensure_redis_url_string(cls, v: str) -> str:
        """Ensure Redis URL is a properly formatted string"""
        if not isinstance(v, str):
            v = str(v)
        # Basic validation of Redis URL format
        if not v.startswith("redis://"):
            raise ValueError("Redis URL must start with 'redis://'")
        return v

    @field_validator("REDIS_DSN", mode='before')
    def validate_redis_dsn(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate Redis URL format using Pydantic's RedisDsn"""
        if v is None:
            return "redis://localhost:6379/0"
        # This will raise ValidationError if invalid
        RedisDsn(str(v))
        return str(v)

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    @field_validator("ALLOWED_ORIGINS", mode='before')
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                loaded = json.loads(v)
                if isinstance(loaded, list):
                    return loaded
            except json.JSONDecodeError:
                return [x.strip() for x in v.split(",")]
        if isinstance(v, list):
            return v
        raise ValueError("ALLOWED_ORIGINS must be a JSON array or comma-separated string.")

    # WebSocket Settings
    WEBSOCKET_IDLE_TIMEOUT_SECONDS: int = 300  # 5 minutes default
    WEBSOCKET_PING_INTERVAL_SECONDS: int = 30   # Regular ping to check connection
    
    # Market Data Providers
    MARKET_DATA_PROVIDER: str = "yahoo_finance"
    YAHOO_FINANCE_ENABLED: bool = True
    ALPHA_VANTAGE_ENABLED: bool = True
    FINNHUB_ENABLED: bool = False
    MARKET_OVERVIEW_INDICES: List[str] = ["^GSPC", "^IXIC", "^DJI"]
    INDEX_NAMES: Dict[str, str] = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "^DJI": "Dow Jones"
    }
    DEFAULT_HISTORICAL_DATA_PERIOD_DAYS: int = 365
    MARKET_DATA_CACHE_TTL_SECONDS: int = 300

    @field_validator("MARKET_OVERVIEW_INDICES", mode='before')
    def parse_market_indices(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("INDEX_NAMES", mode='before')
    def parse_index_names(cls, v: Any) -> Dict[str, str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    # CHAETRA Engine Settings
    CHAETRA_LEARNING_MIN_PATTERN_CONFIDENCE: float = 0.6
    CHAETRA_LEARNING_MIN_VALIDATIONS_FOR_CORE: int = 3
    CHAETRA_LEARNING_SUCCESS_THRESHOLD_PERCENT: float = 1.0
    CHAETRA_TREND_SMA_SHORT_PERIOD: int = 10
    CHAETRA_TREND_SMA_LONG_PERIOD: int = 50
    CHAETRA_MEMORY_VALIDATION_THRESHOLD: int = 3
    CHAETRA_MEMORY_CORE_CONFIDENCE_THRESHOLD: float = 0.8
    CHAETRA_MEMORY_SHORT_TERM_TTL_SECONDS: int = 86400
    CHAETRA_MEMORY_VALIDATION_CONFIDENCE_BOOST: float = 0.1
    CHAETRA_MEMORY_ARCHIVE_CONFIDENCE_THRESHOLD: float = 0.3
    CHAETRA_REASONING_HYPOTHESIS_CONFIDENCE: float = 0.7
    CHAETRA_OPINION_MIN_CONFIDENCE_TO_STORE: float = 0.6

    # Sentiment Analysis
    SENTIMENT_POSITIVE_THRESHOLD: float = 0.15
    SENTIMENT_NEGATIVE_THRESHOLD: float = -0.15

    # Fundamental Analysis
    FUNDAMENTAL_ANALYSIS_DEFAULT_PERIODS: int = 4

    # External API Keys
    ALPHA_VANTAGE_API_KEY: Optional[SecretStr] = None
    YAHOO_FINANCE_API_KEY: Optional[SecretStr] = None
    FINNHUB_API_KEY: Optional[SecretStr] = None

    # LLM Provider Configuration
    DEFAULT_LLM_PROVIDER: str = "gemini"
    LLM_PROVIDER_ORDER: List[str] = ["gemini", "openai", "lm_studio", "ollama"]
    LLM_PROVIDER_CACHE_TTL_SECONDS: int = 3600
    LLM_API_TIMEOUT_SECONDS: int = 30
    
    # LLM Provider Enable Flags
    ENABLE_GEMINI: bool = True
    ENABLE_OPENAI: bool = True
    ENABLE_LM_STUDIO: bool = False
    ENABLE_OLLAMA: bool = False

    # OpenAI Settings
    OPENAI_API_KEY: Optional[SecretStr] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # Gemini Settings
    GEMINI_API_KEY: Optional[SecretStr] = None
    GEMINI_MODEL: str = "gemini-1.5-flash-latest"

    # Ollama Settings
    OLLAMA_API_URL: Optional[str] = None
    OLLAMA_MODEL: Optional[str] = None

    # LM Studio Settings
    LM_STUDIO_BASE_URL: Optional[str] = None
    LM_STUDIO_MODEL: Optional[str] = None

    @field_validator("LLM_PROVIDER_ORDER", mode='before')
    def parse_llm_providers(cls, v: Any) -> List[str]:
        """Parse LLM provider order from string or list"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [x.strip().lower() for x in v.split(",")]
        return v

    @model_validator(mode='after')
    def validate_llm_providers(self) -> 'Settings':
        """Validate LLM providers and ensure at least one is properly configured"""
        enabled_providers = []
        
        # Check each provider's configuration
        # Check each provider and its API key
        if self.ENABLE_GEMINI and self.GEMINI_API_KEY and self.GEMINI_API_KEY.get_secret_value():
            enabled_providers.append("gemini")
            
        if self.ENABLE_OPENAI and self.OPENAI_API_KEY and self.OPENAI_API_KEY.get_secret_value():
            enabled_providers.append("openai")
            
        if self.ENABLE_LM_STUDIO and self.LM_STUDIO_BASE_URL:
            enabled_providers.append("lm_studio")
            
        if self.ENABLE_OLLAMA and self.OLLAMA_API_URL:
            enabled_providers.append("ollama")

        # Filter and update provider order
        filtered_providers = [p for p in self.LLM_PROVIDER_ORDER if p in enabled_providers]
        
        if not filtered_providers:
            raise ValueError("No enabled LLM providers found. Please enable and configure at least one provider.")
        
        self.LLM_PROVIDER_ORDER = filtered_providers
        return self

    # SEC EDGAR Configuration
    SEC_EDGAR_USER_AGENT: str = "MyStockAnalysisApp/1.0 contact@example.com"
    SEC_COMPANY_FACTS_URL: str = "https://data.sec.gov/api/xbrl/companyfacts/"
    SEC_SUBMISSIONS_URL: str = "https://data.sec.gov/submissions/"
    SEC_RATE_LIMIT_PER_SEC: int = 10

    # Technical Analysis
    TECHNICAL_ANALYSIS_DEFAULT_HISTORY_DAYS: int = 365
    DEFAULT_SMA_PERIODS: List[int] = [20, 50, 200]
    DEFAULT_EMA_PERIODS: List[int] = [12, 26]
    DEFAULT_RSI_PERIOD: int = 14
    DEFAULT_MACD_PARAMS: Tuple[int, int, int] = (12, 26, 9)
    DEFAULT_BBANDS_PERIOD: int = 20
    DEFAULT_BBANDS_STDDEV: float = 2.0

    @field_validator("DEFAULT_SMA_PERIODS", "DEFAULT_EMA_PERIODS", mode='before')
    def parse_int_list(cls, v: Any) -> List[int]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("DEFAULT_MACD_PARAMS", mode='before')
    def parse_macd(cls, v: Any) -> Tuple[int, int, int]:
        if isinstance(v, str):
            return tuple(json.loads(v))
        return v

    # Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        arbitrary_types_allowed=True,
        validate_default=True
    )

# Global instance
settings = Settings()

def get_settings():
    return settings
