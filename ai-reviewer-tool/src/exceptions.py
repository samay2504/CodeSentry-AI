"""
Custom exceptions for the AI Code Review Tool.

This module defines specific exception types for different error scenarios,
providing better error handling and debugging capabilities.
"""

from typing import Optional, Dict, Any


class AIReviewerError(Exception):
    """Base exception for all AI Reviewer Tool errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ConfigurationError(AIReviewerError):
    """Raised when there's a configuration issue."""
    pass


class ValidationError(AIReviewerError):
    """Raised when input validation fails."""
    pass


class SecurityError(AIReviewerError):
    """Raised when security validation fails."""
    pass


class IngestionError(AIReviewerError):
    """Raised when codebase ingestion fails."""
    pass


class CodebaseIngestionError(IngestionError):
    """Raised when codebase ingestion fails."""
    pass


class FRDIngestionError(IngestionError):
    """Raised when FRD ingestion fails."""
    pass


class LLMError(AIReviewerError):
    """Raised when LLM operations fail."""
    pass


class LLMProviderError(LLMError):
    """Raised when a specific LLM provider fails."""
    
    def __init__(self, provider: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"LLM Provider '{provider}' failed: {message}", details)
        self.provider = provider


class LLMConnectionError(LLMError):
    """Raised when LLM connection fails."""
    pass


class LLMAuthenticationError(LLMError):
    """Raised when LLM authentication fails."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""
    pass


class AnalysisError(AIReviewerError):
    """Raised when code analysis fails."""
    pass


class SecurityAnalysisError(AnalysisError):
    """Raised when security analysis fails."""
    pass


class PerformanceAnalysisError(AnalysisError):
    """Raised when performance analysis fails."""
    pass


class CodeImprovementError(AIReviewerError):
    """Raised when code improvement fails."""
    pass


class OutputError(AIReviewerError):
    """Raised when output generation fails."""
    pass


class ReportGenerationError(OutputError):
    """Raised when report generation fails."""
    pass


class FileOperationError(AIReviewerError):
    """Raised when file operations fail."""
    pass


class ResourceError(AIReviewerError):
    """Raised when resource limits are exceeded."""
    pass


class TimeoutError(AIReviewerError):
    """Raised when operations timeout."""
    pass


class NetworkError(AIReviewerError):
    """Raised when network operations fail."""
    pass


class CacheError(AIReviewerError):
    """Raised when cache operations fail."""
    pass


class LoggingError(AIReviewerError):
    """Raised when logging operations fail."""
    pass


# Exception mapping for common error patterns
EXCEPTION_MAPPING = {
    'ValueError': ValidationError,
    'FileNotFoundError': FileOperationError,
    'PermissionError': FileOperationError,
    'OSError': FileOperationError,
    'ConnectionError': NetworkError,
    'TimeoutError': TimeoutError,
    'KeyError': ConfigurationError,
    'TypeError': ValidationError,
    'AttributeError': ConfigurationError,
    'ImportError': ConfigurationError,
    'ModuleNotFoundError': ConfigurationError,
}


def wrap_exception(exception: Exception, context: str = "") -> AIReviewerError:
    """Wrap a standard exception in an appropriate AIReviewerError."""
    exception_type = type(exception).__name__
    
    if exception_type in EXCEPTION_MAPPING:
        wrapper_class = EXCEPTION_MAPPING[exception_type]
        message = f"{context}: {str(exception)}" if context else str(exception)
        return wrapper_class(message, {'original_exception': exception_type})
    
    # Default to base AIReviewerError
    message = f"{context}: {str(exception)}" if context else str(exception)
    return AIReviewerError(message, {'original_exception': exception_type})


def handle_llm_error(provider: str, error: Exception) -> LLMProviderError:
    """Handle LLM-specific errors and return appropriate exception."""
    error_message = str(error)
    
    if "authentication" in error_message.lower() or "token" in error_message.lower():
        return LLMAuthenticationError(provider, error_message)
    elif "rate limit" in error_message.lower() or "quota" in error_message.lower():
        return LLMRateLimitError(provider, error_message)
    elif "connection" in error_message.lower() or "timeout" in error_message.lower():
        return LLMConnectionError(provider, error_message)
    else:
        return LLMProviderError(provider, error_message) 