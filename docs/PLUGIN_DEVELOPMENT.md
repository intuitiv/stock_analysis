# CHAETRA Plugin Development Guide

## Introduction

CHAETRA is designed to be extensible through plugins. This guide will help you create your own plugins to extend CHAETRA's capabilities for specific domains.

## Plugin Structure

A CHAETRA plugin consists of:

1. **Plugin Metadata**: `plugin.json` file containing plugin information
2. **Plugin Implementation**: Python module implementing the plugin logic
3. **Configuration Schema**: Validation rules for plugin configuration

### 1. Plugin Metadata

Create a `plugin.json` file in your plugin directory:

```json
{
    "name": "your_plugin_name",
    "version": "1.0.0",
    "description": "Your plugin description",
    "domain": "your_domain",
    "entry_point": "plugin",
    "config_schema": {
        "api_key": {
            "type": "str",
            "required": true,
            "description": "API key for data provider"
        },
        "other_config": {
            "type": "int",
            "required": false,
            "default": 3600
        }
    }
}
```

### 2. Plugin Implementation

Create a Python module (e.g., `plugin.py`) with the following structure:

```python
from typing import Dict, Any
from app.chaetra.utils.plugins import ChaetraPlugin

class YourPlugin(ChaetraPlugin):
    name: str = "your_plugin_name"
    version: str = "1.0.0"
    description: str = "Your plugin description"
    domain: str = "your_domain"
    
    def initialize(self, config: Dict[str, Any]) -> None:
        # Initialize your plugin with config
        self.config = config
        self._setup_clients()
        
    def get_tools(self) -> Dict[str, Any]:
        # Return domain-specific tools
        return {
            "your_tool": self.your_tool
        }
        
    def get_prompts(self) -> Dict[str, str]:
        # Return domain-specific prompt templates
        return {
            "your_prompt": "Your prompt template"
        }
        
    def get_validators(self) -> Dict[str, Any]:
        # Return domain-specific validators
        return {
            "your_data": [
                ValidationRule(
                    field="your_field",
                    rule_type="required"
                )
            ]
        }
```

### 3. Configuration Schema

Define validation rules for your plugin's configuration in the `config_schema` section of `plugin.json`.

## Loading Plugins

To load your plugin, add it to the `CHAETRA_PLUGIN_PATH` environment variable:

```bash
export CHAETRA_PLUGIN_PATH="/path/to/your/plugin"
```

## Example Plugin

See the `plugins/financial` directory for a complete example of a financial analysis plugin.

## Best Practices

- **Modularity**: Keep plugins focused on specific domains
- **Validation**: Use validation rules to ensure data integrity
- **Error Handling**: Gracefully handle errors and log them
- **Documentation**: Provide clear documentation for your plugin's usage

## Contributing Plugins

To contribute your plugin to the CHAETRA ecosystem, submit a pull request to the main repository or publish it as a separate package.
