"""
CHAETRA error classes
"""
from typing import Any, Dict, Optional

class ChaetraError(Exception):
    """Base exception class for CHAETRA"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

class LearningError(ChaetraError):
    """Raised when pattern learning fails"""
    pass

class PatternRecognitionError(ChaetraError):
    """Raised when pattern recognition fails"""
    pass

class MemoryError(ChaetraError):
    """Raised when memory operations fail"""
    pass

class ReasoningError(ChaetraError):
    """Raised when reasoning operations fail"""
    pass

class OpinionError(ChaetraError):
    """Raised when opinion generation fails"""
    pass

class ConfigurationError(ChaetraError):
    """Raised when configuration is invalid"""
    pass

class DependencyError(ChaetraError):
    """Raised when a required dependency is missing or invalid"""
    def __init__(self, dependency: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.dependency = dependency
        super().__init__(
            f"Dependency error for {dependency}: {message}",
            details=details
        )

class ImportError(DependencyError):
    """Raised when an optional import is missing"""
    def __init__(self, module: str, feature: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            dependency=module,
            message=f"Optional module {module} is required for {feature}",
            details=details
        )
