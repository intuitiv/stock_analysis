"""Configuration management for CHAETRA."""
from typing import Dict, Any, Optional
import os
import json
from dataclasses import dataclass
from app.chaetra.utils.errors import ConfigurationError

@dataclass
class ChaetraConfig:
    """Configuration class for CHAETRA."""
    # Memory settings
    memory_cache_url: str = "redis://localhost:6379"
    short_term_ttl: int = 24 * 60 * 60  # 24 hours
    core_memory_threshold: float = 0.8
    validation_threshold: int = 3
    
    # Learning settings
    min_pattern_confidence: float = 0.7
    min_pattern_occurrences: int = 2
    learning_rate: float = 0.1
    
    # Reasoning settings
    reasoning_temperature: float = 0.3
    min_reasoning_confidence: float = 0.7
    max_reasoning_depth: int = 5
    
    # Opinion settings
    opinion_temperature: float = 0.3
    min_opinion_confidence: float = 0.7
    evidence_threshold: int = 3
    
    # LLM settings
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    max_tokens: int = 1000
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    # Logging settings
    log_level: str = "INFO"
    log_dir: str = "logs"
    
    # System settings
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    retries: int = 3

class ConfigManager:
    """Configuration manager for CHAETRA."""
    
    def __init__(self):
        self._config = None
        self._env_prefix = "CHAETRA_"
        
    @property
    def config(self) -> ChaetraConfig:
        """Get the configuration."""
        if self._config is None:
            self._load_config()
        return self._config
    
    def _load_config(self):
        """Load configuration from various sources."""
        # Start with default config
        config_dict = {}
        
        # Load from config file if exists
        config_file = os.getenv(f"{self._env_prefix}CONFIG_FILE", "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                config_dict.update(file_config)
            except Exception as e:
                raise ConfigurationError(
                    f"Error loading config file: {str(e)}",
                    details={"config_file": config_file}
                )
        
        # Override with environment variables
        for field in ChaetraConfig.__dataclass_fields__:
            env_var = f"{self._env_prefix}{field.upper()}"
            if env_var in os.environ:
                value = os.environ[env_var]
                # Convert to appropriate type
                field_type = ChaetraConfig.__dataclass_fields__[field].type
                try:
                    if field_type == bool:
                        value = value.lower() in ('true', '1', 'yes')
                    else:
                        value = field_type(value)
                    config_dict[field] = value
                except ValueError as e:
                    raise ConfigurationError(
                        f"Invalid value for {env_var}: {str(e)}",
                        details={"env_var": env_var, "value": value}
                    )
        
        # Create config object
        try:
            self._config = ChaetraConfig(**config_dict)
        except Exception as e:
            raise ConfigurationError(
                "Error creating config object",
                details={"error": str(e), "config": config_dict}
            )
        
    def reload_config(self):
        """Reload configuration."""
        self._config = None
        return self.config
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        if self._config is None:
            self._load_config()
            
        config_dict = {
            field: getattr(self._config, field)
            for field in self._config.__dataclass_fields__
        }
        config_dict.update(updates)
        
        try:
            self._config = ChaetraConfig(**config_dict)
        except Exception as e:
            raise ConfigurationError(
                "Error updating config",
                details={"error": str(e), "updates": updates}
            )

    def validate_config(self) -> bool:
        """Validate the current configuration."""
        try:
            # Memory settings validation
            if self.config.short_term_ttl <= 0:
                raise ValueError("short_term_ttl must be positive")
            if not 0 <= self.config.core_memory_threshold <= 1:
                raise ValueError("core_memory_threshold must be between 0 and 1")
                
            # Learning settings validation
            if not 0 <= self.config.min_pattern_confidence <= 1:
                raise ValueError("min_pattern_confidence must be between 0 and 1")
            if self.config.min_pattern_occurrences < 1:
                raise ValueError("min_pattern_occurrences must be positive")
                
            # Reasoning settings validation
            if not 0 <= self.config.reasoning_temperature <= 1:
                raise ValueError("reasoning_temperature must be between 0 and 1")
            if not 0 <= self.config.min_reasoning_confidence <= 1:
                raise ValueError("min_reasoning_confidence must be between 0 and 1")
                
            # Opinion settings validation
            if not 0 <= self.config.opinion_temperature <= 1:
                raise ValueError("opinion_temperature must be between 0 and 1")
            if not 0 <= self.config.min_opinion_confidence <= 1:
                raise ValueError("min_opinion_confidence must be between 0 and 1")
                
            # System settings validation
            if self.config.max_concurrent_requests < 1:
                raise ValueError("max_concurrent_requests must be positive")
            if self.config.request_timeout < 1:
                raise ValueError("request_timeout must be positive")
                
            return True
        except Exception as e:
            raise ConfigurationError(
                "Configuration validation failed",
                details={"error": str(e)}
            )

# Create global config manager instance
config_manager = ConfigManager()
