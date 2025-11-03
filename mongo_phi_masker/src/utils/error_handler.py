"""
Error handling utility for MongoDB PHI masking pipeline.

This module provides robust error handling capabilities:
- Exception capturing and reporting
- Error classification and recovery
- Retry mechanisms for transient errors
"""

import sys
import logging
import traceback
import time
from functools import wraps
from typing import Dict, Any, Optional, List, Union, Callable, Type, TypeVar

# Type variable for return type of decorated functions
T = TypeVar('T')


class MaskerError(Exception):
    """Base exception class for the masker application."""
    
    def __init__(self, message: str, code: str = None, details: Dict[str, Any] = None):
        """Initialize the exception.
        
        Args:
            message: Human-readable error message
            code: Error code for categorization
            details: Additional error details
        """
        self.message = message
        self.code = code or 'ERR_UNKNOWN'
        self.details = details or {}
        super().__init__(message)


class ConfigurationError(MaskerError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, 'ERR_CONFIG', details)


class ConnectionError(MaskerError):
    """Exception raised for MongoDB connection errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, 'ERR_CONNECTION', details)


class MaskingError(MaskerError):
    """Exception raised for errors during data masking."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, 'ERR_MASKING', details)


class ValidationError(MaskerError):
    """Exception raised for data validation errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, 'ERR_VALIDATION', details)


class ErrorHandler:
    """Handles application errors and provides recovery mechanisms."""
    
    def __init__(self, logger: logging.Logger, email_alerter=None):
        """Initialize the error handler.
        
        Args:
            logger: Logger instance for error reporting
            email_alerter: Optional email alerter for critical errors
        """
        self.logger = logger
        self.email_alerter = email_alerter
    
    def handle_exception(self, exc: Exception, context: Dict[str, Any] = None) -> None:
        """Handle an exception based on its type.
        
        Args:
            exc: The exception to handle
            context: Optional context information about the error
        """
        context = context or {}
        
        if isinstance(exc, MaskerError):
            self._handle_application_error(exc, context)
        else:
            self._handle_system_error(exc, context)
    
    def _handle_application_error(self, exc: MaskerError, context: Dict[str, Any]) -> None:
        """Handle application-specific errors.
        
        Args:
            exc: The application error
            context: Context information about the error
        """
        error_info = {
            'message': exc.message,
            'code': exc.code,
            'details': exc.details,
            'context': context
        }
        
        self.logger.error(f"Application error: {exc.message} (Code: {exc.code})")
        
        if self.email_alerter and exc.code in ['ERR_CONNECTION', 'ERR_CONFIG']:
            # Send critical errors via email
            self._send_error_alert(error_info)
    
    def _handle_system_error(self, exc: Exception, context: Dict[str, Any]) -> None:
        """Handle system-level exceptions.
        
        Args:
            exc: The system exception
            context: Context information about the error
        """
        error_type = type(exc).__name__
        error_message = str(exc)
        error_stack = traceback.format_exc()
        
        error_info = {
            'type': error_type,
            'message': error_message,
            'stack': error_stack,
            'context': context
        }
        
        self.logger.error(f"System error: {error_type}: {error_message}")
        self.logger.debug(error_stack)
        
        if self.email_alerter:
            # Send system errors via email
            self._send_error_alert(error_info)
    
    def _send_error_alert(self, error_info: Dict[str, Any]) -> None:
        """Send error alerts via email.
        
        Args:
            error_info: Error information dictionary
        """
        if self.email_alerter:
            try:
                self.email_alerter.send_error_alert(error_info)
            except Exception as email_exc:
                self.logger.error(f"Failed to send error alert: {str(email_exc)}")


def retry(exceptions=None, max_attempts=3, delay=1, backoff_factor=2, logger=None):
    """Retry decorator for retrying operations that may fail."""
    if exceptions is None:
        exceptions = (ConnectionError,)
    elif not isinstance(exceptions, tuple):
        # Convert list or single exception to tuple
        exceptions = tuple(exceptions) if hasattr(exceptions, '__iter__') else (exceptions,)
    
    logger = logger or logging.getLogger(__name__)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            # Get function name safely (handle mock objects)
            func_name = getattr(func, "__name__", str(func))
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    # If this was the last attempt, re-raise without logging
                    if attempt == max_attempts:
                        raise
                    
                    # Only log warnings for non-final attempts
                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func_name} "
                        f"due to {type(e).__name__}: {str(e)}"
                    )
                    
                    # Sleep with exponential backoff
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                    attempt += 1
            
            return None  # This should never be reached
        return wrapper
    return decorator


def setup_global_exception_handler(error_handler: ErrorHandler) -> None:
    """Set up a global exception handler to catch unhandled exceptions.
    
    Args:
        error_handler: Error handler instance
    """
    def global_exception_hook(exc_type, exc_value, exc_traceback):
        """Global exception hook to catch unhandled exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Let keyboard interrupts pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_handler.handle_exception(exc_value, {
            'type': exc_type.__name__,
            'traceback': traceback.format_tb(exc_traceback)
        })
    
    # Set the global exception hook
    sys.excepthook = global_exception_hook 