"""Middleware system for CHAETRA."""
from typing import Dict, Any, List, Callable, Optional, TypeVar, Generic, Protocol
from dataclasses import dataclass
import asyncio
from app.chaetra.utils.errors import ConfigurationError
from app.chaetra.utils.logging import CHAETRALogger

logger = CHAETRALogger("middleware")

T = TypeVar('T')  # Request type
R = TypeVar('R')  # Response type

class MiddlewareProtocol(Protocol, Generic[T, R]):
    """Protocol for middleware components."""
    
    async def process_request(self, request: T) -> T:
        """Process the request before main handling."""
        ...
        
    async def process_response(self, request: T, response: R) -> R:
        """Process the response after main handling."""
        ...

@dataclass
class MiddlewareConfig:
    """Configuration for middleware."""
    enabled: bool = True
    order: int = 0
    config: Optional[Dict[str, Any]] = None

class BaseMiddleware(MiddlewareProtocol[T, R]):
    """Base middleware class with default implementations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
    async def process_request(self, request: T) -> T:
        """Default request processing (pass-through)."""
        return request
        
    async def process_response(self, request: T, response: R) -> R:
        """Default response processing (pass-through)."""
        return response

class TimingMiddleware(BaseMiddleware[T, R]):
    """Middleware for timing request/response cycles."""
    
    async def process_request(self, request: T) -> T:
        setattr(request, '_start_time', asyncio.get_event_loop().time())
        return request
        
    async def process_response(self, request: T, response: R) -> R:
        start_time = getattr(request, '_start_time', None)
        if start_time:
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(
                "Request processed",
                {
                    "duration": duration,
                    "request_type": type(request).__name__
                }
            )
        return response

class LoggingMiddleware(BaseMiddleware[T, R]):
    """Middleware for logging requests and responses."""
    
    async def process_request(self, request: T) -> T:
        logger.info(
            "Processing request",
            {
                "request_type": type(request).__name__,
                "request_id": id(request)
            }
        )
        return request
        
    async def process_response(self, request: T, response: R) -> R:
        logger.info(
            "Generated response",
            {
                "request_type": type(request).__name__,
                "request_id": id(request),
                "response_type": type(response).__name__
            }
        )
        return response

class ValidationMiddleware(BaseMiddleware[T, R]):
    """Middleware for request/response validation."""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        request_validator: Optional[Callable[[T], bool]] = None,
        response_validator: Optional[Callable[[R], bool]] = None
    ):
        super().__init__(config)
        self.request_validator = request_validator
        self.response_validator = response_validator
        
    async def process_request(self, request: T) -> T:
        if self.request_validator and not self.request_validator(request):
            raise ValidationError(
                "Request validation failed",
                details={"request_type": type(request).__name__}
            )
        return request
        
    async def process_response(self, request: T, response: R) -> R:
        if self.response_validator and not self.response_validator(response):
            raise ValidationError(
                "Response validation failed",
                details={"response_type": type(response).__name__}
            )
        return response

class MiddlewareManager(Generic[T, R]):
    """Manager for middleware chain."""
    
    def __init__(self):
        self.middlewares: List[tuple[MiddlewareProtocol[T, R], MiddlewareConfig]] = []
        
    def add_middleware(
        self,
        middleware: MiddlewareProtocol[T, R],
        config: Optional[MiddlewareConfig] = None
    ) -> None:
        """Add middleware to the chain."""
        if not config:
            config = MiddlewareConfig()
            
        self.middlewares.append((middleware, config))
        # Sort by order
        self.middlewares.sort(key=lambda x: x[1].order)
        
    async def process_request(self, request: T) -> T:
        """Process request through middleware chain."""
        current_request = request
        for middleware, config in self.middlewares:
            if config.enabled:
                try:
                    current_request = await middleware.process_request(current_request)
                except Exception as e:
                    logger.error(
                        "Middleware request processing failed",
                        error=e,
                        data={
                            "middleware": type(middleware).__name__,
                            "request_type": type(request).__name__
                        }
                    )
                    raise
        return current_request
        
    async def process_response(self, request: T, response: R) -> R:
        """Process response through middleware chain."""
        current_response = response
        # Process in reverse order
        for middleware, config in reversed(self.middlewares):
            if config.enabled:
                try:
                    current_response = await middleware.process_response(
                        request,
                        current_response
                    )
                except Exception as e:
                    logger.error(
                        "Middleware response processing failed",
                        error=e,
                        data={
                            "middleware": type(middleware).__name__,
                            "response_type": type(response).__name__
                        }
                    )
                    raise
        return current_response

# Create default middleware instances
timing_middleware = TimingMiddleware()
logging_middleware = LoggingMiddleware()

# Create global middleware manager instance
middleware_manager = MiddlewareManager()

# Add default middleware
middleware_manager.add_middleware(
    timing_middleware,
    MiddlewareConfig(order=0)
)
middleware_manager.add_middleware(
    logging_middleware,
    MiddlewareConfig(order=1)
)
