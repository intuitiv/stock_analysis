# Module Development Guide

## Overview

This guide explains how to develop new modules and plugins for the NAETRA/CHAETRA system. The system is designed to be highly modular, allowing easy extension of functionality through well-defined interfaces.

## Core Interfaces

### 1. Data Collector Interface
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class IDataCollector(ABC):
    """Interface for data collection modules"""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the collector with configuration"""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Fetch market data for a symbol"""
        pass
    
    @abstractmethod
    async def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Fetch fundamental data for a symbol"""
        pass

# Example Implementation
class YahooFinanceCollector(IDataCollector):
    def __init__(self):
        self.client = None
        
    async def initialize(self, config: Dict[str, Any]) -> None:
        self.client = YahooFinanceClient(
            api_key=config["api_key"],
            timeout=config.get("timeout", 30)
        )
    
    async def get_market_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        return await self.client.get_historical_data(symbol, timeframe)
    
    async def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        return await self.client.get_company_info(symbol)
```

### 2. Analysis Interface
```python
class IAnalyzer(ABC):
    """Interface for analysis modules"""
    
    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Analysis:
        """Perform analysis on provided data"""
        pass
    
    @abstractmethod
    async def validate(self, analysis: Analysis) -> bool:
        """Validate analysis results"""
        pass

# Example Implementation
class TechnicalAnalyzer(IAnalyzer):
    async def analyze(self, data: Dict[str, Any]) -> Analysis:
        patterns = self.find_patterns(data)
        trends = self.analyze_trends(data)
        indicators = self.calculate_indicators(data)
        
        return Analysis(
            patterns=patterns,
            trends=trends,
            indicators=indicators
        )
    
    async def validate(self, analysis: Analysis) -> bool:
        return self.validate_patterns(analysis.patterns) and \
               self.validate_trends(analysis.trends)
```

### 3. LLM Provider Interface
```python
class ILLMProvider(ABC):
    """Interface for LLM integration"""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the LLM provider"""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate response from LLM"""
        pass

# Example Implementation
class OllamaProvider(ILLMProvider):
    async def initialize(self, config: Dict[str, Any]) -> None:
        self.client = OllamaClient(
            host=config["api_url"],
            model=config["model_name"]
        )
    
    async def generate(self, prompt: str, context: Dict[str, Any]) -> str:
        response = await self.client.complete(
            prompt=prompt,
            context=context,
            temperature=0.7
        )
        return response.text
```

### 4. Storage Interface
```python
class IStorage(ABC):
    """Interface for storage backends"""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize storage connection"""
        pass
    
    @abstractmethod
    async def store(self, key: str, data: Any) -> None:
        """Store data"""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Any:
        """Retrieve data"""
        pass

# Example Implementation
class PostgresStorage(IStorage):
    async def initialize(self, config: Dict[str, Any]) -> None:
        self.pool = await create_pool(
            host=config["host"],
            database=config["database"],
            user=config["user"],
            password=config["password"]
        )
    
    async def store(self, key: str, data: Any) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO data (key, value) VALUES ($1, $2)",
                key, json.dumps(data)
            )
    
    async def retrieve(self, key: str) -> Any:
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT value FROM data WHERE key = $1",
                key
            )
            return json.loads(result["value"]) if result else None
```

## Plugin Registration

### 1. Configuration
```yaml
plugins:
  data_collectors:
    - name: yahoo_finance
      class: collectors.yahoo.YahooFinanceCollector
      enabled: true
      config:
        api_key: "xxx"
        timeout: 30
    
    - name: alpha_vantage
      class: collectors.alpha_vantage.AlphaVantageCollector
      enabled: false
      config:
        api_key: "xxx"
  
  analyzers:
    - name: technical
      class: analyzers.technical.TechnicalAnalyzer
      enabled: true
      config:
        indicators: ["MA", "RSI", "MACD"]
    
    - name: fundamental
      class: analyzers.fundamental.FundamentalAnalyzer
      enabled: true
```

### 2. Plugin Manager
```python
class PluginManager:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.plugins: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize all enabled plugins"""
        for category, plugins in self.config["plugins"].items():
            self.plugins[category] = {}
            for plugin in plugins:
                if plugin["enabled"]:
                    instance = await self.load_plugin(plugin)
                    self.plugins[category][plugin["name"]] = instance
    
    async def load_plugin(self, plugin_config: Dict[str, Any]) -> Any:
        """Load and initialize a plugin"""
        module_path, class_name = plugin_config["class"].rsplit(".", 1)
        module = importlib.import_module(module_path)
        plugin_class = getattr(module, class_name)
        
        instance = plugin_class()
        await instance.initialize(plugin_config.get("config", {}))
        return instance
    
    def get_plugin(self, category: str, name: str) -> Any:
        """Get a plugin instance"""
        return self.plugins[category][name]
```

## Creating New Plugins

### 1. Directory Structure
```
plugins/
├── data_collectors/
│   ├── __init__.py
│   ├── yahoo_finance.py
│   └── alpha_vantage.py
├── analyzers/
│   ├── __init__.py
│   ├── technical.py
│   └── fundamental.py
└── storage/
    ├── __init__.py
    ├── postgres.py
    └── redis.py
```

### 2. Example Implementation Steps

1. **Create Plugin Class**
```python
# plugins/data_collectors/custom_source.py
from core.interfaces import IDataCollector

class CustomDataCollector(IDataCollector):
    async def initialize(self, config: Dict[str, Any]) -> None:
        # Initialize your collector
        self.client = YourCustomClient(config)
    
    async def get_market_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        # Implement data collection
        return await self.client.get_data(symbol, timeframe)
    
    async def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        # Implement fundamentals collection
        return await self.client.get_fundamentals(symbol)
```

2. **Add Configuration**
```yaml
plugins:
  data_collectors:
    - name: custom_source
      class: plugins.data_collectors.custom_source.CustomDataCollector
      enabled: true
      config:
        api_key: "xxx"
        base_url: "https://api.custom-source.com"
```

3. **Register Plugin**
```python
# In your application initialization
plugin_manager = PluginManager("config.yaml")
await plugin_manager.initialize()

# Use the plugin
collector = plugin_manager.get_plugin("data_collectors", "custom_source")
data = await collector.get_market_data("AAPL", "1D")
```

## Best Practices

1. **Error Handling**
```python
class CustomPlugin(IPlugin):
    async def operation(self) -> Result:
        try:
            # Perform operation
            result = await self.do_something()
            return result
        except ConnectionError as e:
            logger.error(f"Connection failed: {e}")
            raise PluginError("Connection failed")
        except ValueError as e:
            logger.error(f"Invalid data: {e}")
            raise PluginError("Invalid data")
```

2. **Logging**
```python
import logging

logger = logging.getLogger(__name__)

class CustomPlugin(IPlugin):
    async def initialize(self, config: Dict[str, Any]) -> None:
        logger.info(f"Initializing {self.__class__.__name__}")
        try:
            await self.setup(config)
            logger.info(f"{self.__class__.__name__} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise
```

3. **Configuration Validation**
```python
class CustomPlugin(IPlugin):
    def validate_config(self, config: Dict[str, Any]) -> None:
        required_fields = ["api_key", "base_url"]
        for field in required_fields:
            if field not in config:
                raise ConfigurationError(f"Missing required field: {field}")
```

4. **Resource Management**
```python
class CustomPlugin(IPlugin):
    async def initialize(self, config: Dict[str, Any]) -> None:
        self.client = await self.create_client(config)
        
    async def cleanup(self) -> None:
        if self.client:
            await self.client.close()
```

## Testing Plugins

### 1. Unit Tests
```python
import pytest
from unittest.mock import Mock, patch

def test_custom_plugin():
    plugin = CustomPlugin()
    config = {"api_key": "test", "base_url": "http://test"}
    
    with patch("custom_plugin.Client") as mock_client:
        await plugin.initialize(config)
        assert plugin.client == mock_client.return_value
        
        result = await plugin.operation()
        assert result.status == "success"
```

### 2. Integration Tests
```python
@pytest.mark.integration
async def test_plugin_integration():
    plugin = CustomPlugin()
    config = load_test_config()
    
    await plugin.initialize(config)
    result = await plugin.operation()
    
    assert result.status == "success"
    assert isinstance(result.data, dict)
```

## Deployment

### 1. Plugin Packaging
```toml
# pyproject.toml
[tool.poetry]
name = "custom-plugin"
version = "0.1.0"
description = "Custom plugin for NAETRA"
packages = [
    { include = "plugins" }
]

[tool.poetry.dependencies]
python = "^3.9"
aiohttp = "^3.8.0"
```

### 2. Installation
```bash
# Install plugin
pip install custom-plugin

# Update configuration
echo '
plugins:
  custom:
    - name: custom_plugin
      class: plugins.custom.CustomPlugin
      enabled: true
      config:
        key: "value"
' >> config.yaml
```

## Monitoring

### 1. Health Checks
```python
class CustomPlugin(IPlugin):
    async def health_check(self) -> bool:
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
```

### 2. Metrics
```python
from prometheus_client import Counter, Histogram

class CustomPlugin(IPlugin):
    def __init__(self):
        self.operation_counter = Counter(
            'plugin_operations_total',
            'Total operations performed'
        )
        self.operation_duration = Histogram(
            'plugin_operation_duration_seconds',
            'Operation duration in seconds'
        )
```

## Documentation

### 1. Plugin Documentation
```python
class CustomPlugin(IPlugin):
    """Custom plugin for specific functionality.
    
    This plugin implements specific functionality for the system.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
    """
    
    async def operation(self) -> Result:
        """Perform the main operation.
        
        Args:
            None
            
        Returns:
            Result: Operation result
            
        Raises:
            PluginError: If operation fails
        """
        pass
```

### 2. Configuration Documentation
```yaml
# config.yaml
plugins:
  custom:
    - name: custom_plugin
      class: plugins.custom.CustomPlugin
      enabled: true
      config:
        # API key for authentication
        api_key: "xxx"
        
        # Base URL for API requests
        base_url: "https://api.example.com"
        
        # Timeout in seconds
        timeout: 30
        
        # Retry configuration
        retries:
          max_attempts: 3
          delay: 1
