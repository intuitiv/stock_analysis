"""Plugin system for CHAETRA."""
from typing import Dict, Any, List, Type, Optional, Protocol, runtime_checkable
from dataclasses import dataclass
import importlib
import os
import json
from app.chaetra.utils.errors import ConfigurationError
from app.chaetra.utils.logging import CHAETRALogger

logger = CHAETRALogger("plugins")

@runtime_checkable
class ChaetraPlugin(Protocol):
    """Protocol defining what a CHAETRA plugin must implement."""
    
    name: str
    version: str
    description: str
    domain: str
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration."""
        ...
        
    def get_tools(self) -> Dict[str, Any]:
        """Get domain-specific tools provided by this plugin."""
        ...
        
    def get_prompts(self) -> Dict[str, str]:
        """Get domain-specific prompt templates."""
        ...
        
    def get_validators(self) -> Dict[str, Any]:
        """Get domain-specific validators."""
        ...

@dataclass
class PluginInfo:
    """Plugin metadata."""
    name: str
    version: str
    description: str
    domain: str
    entry_point: str
    config_schema: Dict[str, Any]

class PluginManager:
    """Manager for CHAETRA plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, ChaetraPlugin] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        
    def load_plugin(
        self,
        plugin_path: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Load a plugin from a path."""
        try:
            # Load plugin metadata
            metadata_path = os.path.join(plugin_path, "plugin.json")
            if not os.path.exists(metadata_path):
                raise ConfigurationError(
                    "Plugin metadata not found",
                    details={"path": metadata_path}
                )
                
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            plugin_info = PluginInfo(
                name=metadata["name"],
                version=metadata["version"],
                description=metadata["description"],
                domain=metadata["domain"],
                entry_point=metadata["entry_point"],
                config_schema=metadata.get("config_schema", {})
            )
            
            # Validate plugin configuration
            if config:
                self._validate_plugin_config(plugin_info, config)
            
            # Import plugin module
            module_path = f"{plugin_path.replace('/', '.')}.{plugin_info.entry_point}"
            plugin_module = importlib.import_module(module_path)
            
            # Get plugin class
            plugin_class = getattr(plugin_module, "Plugin")
            
            # Initialize plugin
            plugin = plugin_class()
            if not isinstance(plugin, ChaetraPlugin):
                raise ConfigurationError(
                    "Invalid plugin implementation",
                    details={"plugin": plugin_info.name}
                )
                
            # Initialize plugin with config
            plugin.initialize(config or {})
            
            # Store plugin
            self._plugins[plugin_info.name] = plugin
            self._plugin_configs[plugin_info.name] = config or {}
            
            logger.info(
                f"Loaded plugin: {plugin_info.name}",
                {"version": plugin_info.version, "domain": plugin_info.domain}
            )
            
        except Exception as e:
            raise ConfigurationError(
                f"Error loading plugin from {plugin_path}",
                details={"error": str(e)}
            )
            
    def get_plugin(self, name: str) -> Optional[ChaetraPlugin]:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)
        
    def get_all_plugins(self) -> Dict[str, ChaetraPlugin]:
        """Get all loaded plugins."""
        return self._plugins.copy()
        
    def get_plugins_for_domain(self, domain: str) -> List[ChaetraPlugin]:
        """Get all plugins for a specific domain."""
        return [
            plugin for plugin in self._plugins.values()
            if plugin.domain == domain
        ]
        
    def _validate_plugin_config(
        self,
        plugin_info: PluginInfo,
        config: Dict[str, Any]
    ) -> None:
        """Validate plugin configuration against schema."""
        schema = plugin_info.config_schema
        
        for key, value_schema in schema.items():
            if value_schema.get("required", False) and key not in config:
                raise ConfigurationError(
                    f"Missing required config: {key}",
                    details={
                        "plugin": plugin_info.name,
                        "missing_key": key
                    }
                )
            
            if key in config:
                value = config[key]
                value_type = value_schema.get("type")
                if value_type and not isinstance(value, eval(value_type)):
                    raise ConfigurationError(
                        f"Invalid config type for {key}",
                        details={
                            "plugin": plugin_info.name,
                            "key": key,
                            "expected_type": value_type,
                            "actual_type": type(value).__name__
                        }
                    )

class PluginTools:
    """Utility class for working with plugin tools."""
    
    @staticmethod
    def merge_tools(
        tools_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Merge tools from multiple plugins."""
        merged = {}
        for tools in tools_list:
            for name, tool in tools.items():
                if name in merged:
                    logger.warning(f"Tool {name} already exists, skipping")
                    continue
                merged[name] = tool
        return merged

    @staticmethod
    def merge_prompts(
        prompts_list: List[Dict[str, str]]
    ) -> Dict[str, str]:
        """Merge prompts from multiple plugins."""
        merged = {}
        for prompts in prompts_list:
            for name, prompt in prompts.items():
                if name in merged:
                    logger.warning(f"Prompt {name} already exists, skipping")
                    continue
                merged[name] = prompt
        return merged

# Create global plugin manager instance
plugin_manager = PluginManager()
