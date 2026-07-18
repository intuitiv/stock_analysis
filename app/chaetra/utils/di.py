"""Dependency injection container for CHAETRA."""
from typing import Dict, Any, Type, Optional
from dataclasses import dataclass
from app.chaetra.utils.errors import ConfigurationError

@dataclass
class ServiceProvider:
    """Service provider configuration."""
    service_class: Type
    singleton: bool = True
    args: Optional[Dict[str, Any]] = None
    kwargs: Optional[Dict[str, Any]] = None

class DIContainer:
    """Dependency injection container."""
    
    def __init__(self):
        self._providers: Dict[str, ServiceProvider] = {}
        self._instances: Dict[str, Any] = {}
        
    def register(
        self,
        service_name: str,
        service_class: Type,
        singleton: bool = True,
        args: Optional[Dict[str, Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a service with the container."""
        self._providers[service_name] = ServiceProvider(
            service_class=service_class,
            singleton=singleton,
            args=args or {},
            kwargs=kwargs or {}
        )
        
    def get(self, service_name: str) -> Any:
        """Get a service instance."""
        if service_name not in self._providers:
            raise ConfigurationError(
                f"No provider registered for service: {service_name}",
                details={"available_services": list(self._providers.keys())}
            )
            
        provider = self._providers[service_name]
        
        # Return existing instance if singleton
        if provider.singleton and service_name in self._instances:
            return self._instances[service_name]
            
        # Create new instance
        try:
            instance = provider.service_class(
                *provider.args.values(),
                **provider.kwargs
            )
            
            # Store if singleton
            if provider.singleton:
                self._instances[service_name] = instance
                
            return instance
        except Exception as e:
            raise ConfigurationError(
                f"Error creating service instance: {service_name}",
                details={
                    "error": str(e),
                    "service_class": provider.service_class.__name__,
                    "args": provider.args,
                    "kwargs": provider.kwargs
                }
            )
            
    def get_all(self) -> Dict[str, Any]:
        """Get all registered services."""
        return {
            name: self.get(name)
            for name in self._providers.keys()
        }
        
    def has_service(self, service_name: str) -> bool:
        """Check if a service is registered."""
        return service_name in self._providers
        
    def remove_service(self, service_name: str) -> None:
        """Remove a service from the container."""
        if service_name in self._providers:
            del self._providers[service_name]
        if service_name in self._instances:
            del self._instances[service_name]
            
    def clear(self) -> None:
        """Clear all services and instances."""
        self._providers.clear()
        self._instances.clear()

class ServiceLocator:
    """Service locator pattern implementation."""
    
    _instance = None
    _container: Optional[DIContainer] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._container = DIContainer()
        return cls._instance
    
    @classmethod
    def get_container(cls) -> DIContainer:
        """Get the DI container."""
        if cls._container is None:
            cls._container = DIContainer()
        return cls._container
    
    @classmethod
    def register_core_services(cls) -> None:
        """Register core CHAETRA services."""
        container = cls.get_container()
        
        from app.chaetra.memory import MemorySystem
        from app.chaetra.learning import LearningSystem
        from app.chaetra.reasoning import ReasoningSystem
        from app.chaetra.opinion import OpinionSystem
        from app.chaetra.llm import LLMManager
        from app.chaetra.brain import CHAETRA
        from app.core.cache import RedisCache
        from app.chaetra.utils.config import config_manager
        
        # Register core services
        container.register("config", type(config_manager), singleton=True)
        container.register("cache", RedisCache, singleton=True)
        container.register("memory", MemorySystem, singleton=True)
        container.register("llm", LLMManager, singleton=True)
        container.register("learning", LearningSystem, singleton=True)
        container.register("reasoning", ReasoningSystem, singleton=True)
        container.register("opinion", OpinionSystem, singleton=True)
        container.register("brain", CHAETRA, singleton=True)

# Create global service locator instance
service_locator = ServiceLocator()
