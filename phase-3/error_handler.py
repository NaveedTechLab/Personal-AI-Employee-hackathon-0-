"""
Error Handler Module for Phase 3 - Autonomous Employee (Gold Tier)
Provides comprehensive error handling and recovery mechanisms for different error categories.
"""

import asyncio
import traceback
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
import logging
from functools import wraps
import sys
import signal


class ErrorCategory(Enum):
    """Enumeration of different error categories."""
    TRANSIENT = "transient"
    AUTHENTICATION = "authentication"
    LOGIC = "logic"
    DATA = "data"
    SYSTEM = "system"


class RecoveryStrategy(Enum):
    """Enumeration of different recovery strategies."""
    RETRY = "retry"
    FALLBACK = "fallback"
    HALT = "halt"
    NOTIFY_HUMAN = "notify_human"
    SKIP = "skip"


@dataclass
class ErrorInfo:
    """Information about an error occurrence."""
    error_id: str
    error_category: ErrorCategory
    error_message: str
    error_traceback: str
    timestamp: datetime
    context: Dict[str, Any]
    recovery_strategy: RecoveryStrategy
    attempts_made: int = 0
    max_attempts: int = 0
    recovered: bool = False


class ErrorHandler:
    """
    Class responsible for handling different error categories with appropriate
    recovery strategies and graceful degradation.
    """

    def __init__(self, max_retry_attempts: Dict[ErrorCategory, int] = None, retry_delay: timedelta = timedelta(seconds=5)):
        """
        Initialize the ErrorHandler.

        Args:
            max_retry_attempts: Maximum retry attempts per error category
            retry_delay: Delay between retry attempts
        """
        self.max_retry_attempts = max_retry_attempts or {
            ErrorCategory.TRANSIENT: 3,
            ErrorCategory.AUTHENTICATION: 1,
            ErrorCategory.LOGIC: 0,  # No retries for logic errors
            ErrorCategory.DATA: 2,
            ErrorCategory.SYSTEM: 2
        }
        self.retry_delay = retry_delay
        self.errors: List[ErrorInfo] = []
        self.fallback_functions: Dict[ErrorCategory, Callable] = {}
        self.human_notification_callback: Optional[Callable] = None
        self.halt_on_critical_errors = True

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def register_fallback_function(self, error_category: ErrorCategory, fallback_func: Callable):
        """
        Register a fallback function for a specific error category.

        Args:
            error_category: The error category to register the fallback for
            fallback_func: The fallback function to call
        """
        self.fallback_functions[error_category] = fallback_func
        self.logger.info(f"Registered fallback function for error category: {error_category.value}")

    def set_human_notification_callback(self, callback: Callable):
        """
        Set a callback function to notify humans of critical errors.

        Args:
            callback: The callback function to notify humans
        """
        self.human_notification_callback = callback
        self.logger.info("Registered human notification callback")

    def handle_error(self, error: Exception, context: Dict[str, Any] = None, error_category: ErrorCategory = None) -> ErrorInfo:
        """
        Handle an error based on its category and context.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            error_category: Category of the error (if known)

        Returns:
            ErrorInfo object with details about the error handling
        """
        if context is None:
            context = {}

        # Determine error category if not provided
        if error_category is None:
            error_category = self._categorize_error(error)

        # Create error info
        error_id = f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(error)) % 10000:04d}"
        error_traceback = traceback.format_exc()

        error_info = ErrorInfo(
            error_id=error_id,
            error_category=error_category,
            error_message=str(error),
            error_traceback=error_traceback,
            timestamp=datetime.now(),
            context=context,
            recovery_strategy=self._determine_recovery_strategy(error_category),
            max_attempts=self.max_retry_attempts.get(error_category, 0)
        )

        self.logger.error(f"Error occurred: {error_info.error_message} (Category: {error_category.value})")
        self.logger.debug(f"Error traceback: {error_traceback}")

        # Add to error log
        self.errors.append(error_info)

        # Execute recovery strategy
        recovered = self._execute_recovery_strategy(error_info)
        error_info.recovered = recovered

        return error_info

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """
        Categorize an error based on its type and message.

        Args:
            error: The exception to categorize

        Returns:
            ErrorCategory for the error
        """
        error_str = str(error).lower()

        # Check for authentication-related errors
        auth_keywords = ['auth', 'token', 'credential', 'login', 'password', 'unauthorized', 'forbidden']
        if any(keyword in error_str for keyword in auth_keywords):
            return ErrorCategory.AUTHENTICATION

        # Check for data-related errors
        data_keywords = ['json', 'parse', 'decode', 'invalid', 'malformed', 'data', 'format']
        if any(keyword in error_str for keyword in data_keywords):
            return ErrorCategory.DATA

        # Check for system-related errors
        system_keywords = ['connection', 'network', 'timeout', 'socket', 'system', 'resource']
        if any(keyword in error_str for keyword in system_keywords):
            return ErrorCategory.SYSTEM

        # Check for transient errors
        transient_keywords = ['temporary', 'retry', 'try again', 'momentarily unavailable']
        if any(keyword in error_str for keyword in transient_keywords):
            return ErrorCategory.TRANSIENT

        # Check for logic errors (ValueError, TypeError, etc.)
        if isinstance(error, (ValueError, TypeError, AttributeError)):
            return ErrorCategory.LOGIC

        # Default to system error
        return ErrorCategory.SYSTEM

    def _determine_recovery_strategy(self, error_category: ErrorCategory) -> RecoveryStrategy:
        """
        Determine the appropriate recovery strategy for an error category.

        Args:
            error_category: The category of the error

        Returns:
            RecoveryStrategy for the error
        """
        strategy_map = {
            ErrorCategory.TRANSIENT: RecoveryStrategy.RETRY,
            ErrorCategory.AUTHENTICATION: RecoveryStrategy.NOTIFY_HUMAN,
            ErrorCategory.LOGIC: RecoveryStrategy.HALT,
            ErrorCategory.DATA: RecoveryStrategy.FALLBACK,
            ErrorCategory.SYSTEM: RecoveryStrategy.RETRY
        }

        return strategy_map.get(error_category, RecoveryStrategy.HALT)

    def _execute_recovery_strategy(self, error_info: ErrorInfo) -> bool:
        """
        Execute the recovery strategy for an error.

        Args:
            error_info: Information about the error to recover from

        Returns:
            True if recovery was successful, False otherwise
        """
        strategy = error_info.recovery_strategy
        category = error_info.error_category

        self.logger.info(f"Executing recovery strategy '{strategy.value}' for error category '{category.value}'")

        if strategy == RecoveryStrategy.RETRY:
            return self._handle_retry(error_info)
        elif strategy == RecoveryStrategy.FALLBACK:
            return self._handle_fallback(category, error_info.context)
        elif strategy == RecoveryStrategy.HALT:
            return self._handle_halt(error_info)
        elif strategy == RecoveryStrategy.NOTIFY_HUMAN:
            return self._handle_notify_human(error_info)
        elif strategy == RecoveryStrategy.SKIP:
            self.logger.info(f"Skipping action due to error: {error_info.error_message}")
            return True  # Consider this as "handled" since we're skipping

        return False

    def _handle_retry(self, error_info: ErrorInfo) -> bool:
        """
        Handle retry strategy for transient and system errors.

        Args:
            error_info: Information about the error to retry

        Returns:
            True if retry was successful, False otherwise
        """
        max_attempts = self.max_retry_attempts.get(error_info.error_category, 0)

        if error_info.attempts_made >= max_attempts:
            self.logger.error(f"Max retry attempts ({max_attempts}) exceeded for error: {error_info.error_id}")
            return False

        self.logger.info(f"Retrying action (attempt {error_info.attempts_made + 1}/{max_attempts})...")
        error_info.attempts_made += 1

        # Wait before retry
        delay_seconds = self.retry_delay.total_seconds() * (2 ** (error_info.attempts_made - 1))  # Exponential backoff
        asyncio.sleep(delay_seconds)

        return True  # Placeholder - actual retry logic would be implemented elsewhere

    def _handle_fallback(self, error_category: ErrorCategory, context: Dict[str, Any]) -> bool:
        """
        Handle fallback strategy for data errors.

        Args:
            error_category: The error category
            context: Context of the error

        Returns:
            True if fallback was successful, False otherwise
        """
        if error_category in self.fallback_functions:
            try:
                fallback_func = self.fallback_functions[error_category]
                fallback_func(context)
                self.logger.info(f"Fallback executed successfully for category: {error_category.value}")
                return True
            except Exception as fallback_error:
                self.logger.error(f"Fallback function failed: {str(fallback_error)}")
                return False
        else:
            self.logger.warning(f"No fallback function registered for category: {error_category.value}")
            return False

    def _handle_halt(self, error_info: ErrorInfo) -> bool:
        """
        Handle halt strategy for logic errors.

        Args:
            error_info: Information about the error to halt on

        Returns:
            False (since halting means no recovery)
        """
        self.logger.critical(f"Critical error requires halt: {error_info.error_message}")

        if self.halt_on_critical_errors:
            # Notify human if callback is available
            if self.human_notification_callback:
                try:
                    self.human_notification_callback(error_info)
                except Exception as e:
                    self.logger.error(f"Failed to notify human: {str(e)}")

            # In a real system, you might want to shut down gracefully
            # For now, we'll just return False to indicate no recovery
            return False

        return False

    def _handle_notify_human(self, error_info: ErrorInfo) -> bool:
        """
        Handle human notification for authentication errors.

        Args:
            error_info: Information about the error to notify about

        Returns:
            True if notification was sent, False otherwise
        """
        if self.human_notification_callback:
            try:
                self.human_notification_callback(error_info)
                self.logger.info(f"Human notified about error: {error_info.error_id}")
                return True
            except Exception as notify_error:
                self.logger.error(f"Failed to notify human: {str(notify_error)}")
                return False
        else:
            self.logger.warning("No human notification callback registered")
            return False

    def wrap_with_error_handling(self, error_category: ErrorCategory, context: Dict[str, Any] = None):
        """
        Decorator to wrap functions with error handling.

        Args:
            error_category: Category of errors expected from the function
            context: Context to include in error logs
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    ctx = context or {}
                    ctx.update({'function': func.__name__, 'args': str(args)[:100], 'kwargs': str(kwargs)[:100]})

                    error_info = self.handle_error(e, ctx, error_category)

                    if error_info.recovery_strategy == RecoveryStrategy.HALT:
                        raise e  # Re-raise critical errors

                    # For other errors, return None or a default value
                    return None
            return wrapper
        return decorator

    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about handled errors.

        Returns:
            Dictionary with error statistics
        """
        stats = {
            'total_errors': len(self.errors),
            'by_category': {},
            'recovery_success_rate': 0.0,
            'recent_errors': []
        }

        # Count errors by category
        for error in self.errors:
            category = error.error_category.value
            if category not in stats['by_category']:
                stats['by_category'][category] = 0
            stats['by_category'][category] += 1

        # Calculate recovery success rate
        if self.errors:
            recovered_count = sum(1 for error in self.errors if error.recovered)
            stats['recovery_success_rate'] = recovered_count / len(self.errors)

        # Include recent errors (last 10)
        stats['recent_errors'] = [
            {
                'id': error.error_id,
                'category': error.error_category.value,
                'message': error.error_message[:100],
                'timestamp': error.timestamp.isoformat(),
                'recovered': error.recovered
            }
            for error in self.errors[-10:]
        ]

        return stats

    def cleanup_old_errors(self, days_to_keep: int = 30) -> int:
        """
        Remove error records older than the specified number of days.

        Args:
            days_to_keep: Number of days to keep error records

        Returns:
            Number of records removed
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        old_errors = [error for error in self.errors if error.timestamp < cutoff_date]
        for error in old_errors:
            self.errors.remove(error)

        return len(old_errors)

    def shutdown(self):
        """Perform cleanup operations before shutdown."""
        self.logger.info("ErrorHandler shutting down")
        # Perform any necessary cleanup here


def get_error_handler_instance() -> ErrorHandler:
    """
    Factory function to get an ErrorHandler instance.

    Returns:
        ErrorHandler instance
    """
    from .config import ERROR_HANDLING as config

    max_retries = {
        ErrorCategory.TRANSIENT: config['retry_attempts']['transient'],
        ErrorCategory.AUTHENTICATION: config['retry_attempts']['authentication'],
        ErrorCategory.LOGIC: config['retry_attempts']['logic'],
        ErrorCategory.DATA: config['retry_attempts']['data'],
        ErrorCategory.SYSTEM: config['retry_attempts']['system']
    }

    retry_delay = timedelta(seconds=5)  # Default delay

    return ErrorHandler(max_retry_attempts=max_retries, retry_delay=retry_delay)


def graceful_degradation(error_categories: List[ErrorCategory] = None):
    """
    Decorator to implement graceful degradation for specified error categories.

    Args:
        error_categories: List of error categories to handle with graceful degradation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_error_handler_instance()

            # If no specific categories provided, handle all categories
            categories = error_categories or list(ErrorCategory)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Determine if this error category should use graceful degradation
                error_cat = handler._categorize_error(e)

                if error_cat in categories:
                    # Log the error but continue execution gracefully
                    handler.handle_error(e, {
                        'function': func.__name__,
                        'graceful_degradation_applied': True
                    }, error_cat)

                    # Return a safe default value instead of raising the exception
                    return None
                else:
                    # For other categories, re-raise the exception
                    raise
        return wrapper
    return decorator


if __name__ == "__main__":
    import time

    # Example usage
    handler = get_error_handler_instance()

    # Register a fallback function for data errors
    def data_error_fallback(context):
        print(f"Executing fallback for data error in context: {context}")
        # In a real implementation, this would provide default data
        return {"default": "data"}

    handler.register_fallback_function(ErrorCategory.DATA, data_error_fallback)

    # Register a human notification callback
    def notify_human(error_info):
        print(f"URGENT: Human intervention needed for error {error_info.error_id}")
        print(f"Category: {error_info.error_category.value}")
        print(f"Message: {error_info.error_message}")

    handler.set_human_notification_callback(notify_human)

    # Test different error categories
    print("Testing transient error handling...")
    try:
        raise ConnectionError("Network temporarily unavailable, try again")
    except Exception as e:
        handler.handle_error(e, {"operation": "network_call"})

    print("\nTesting data error handling...")
    try:
        raise ValueError("Invalid data format in JSON response")
    except Exception as e:
        handler.handle_error(e, {"operation": "data_processing"})

    print("\nTesting authentication error handling...")
    try:
        raise PermissionError("Unauthorized access - invalid token")
    except Exception as e:
        handler.handle_error(e, {"operation": "api_call"})

    print("\nTesting logic error handling...")
    try:
        raise AttributeError("Object has no attribute 'method'")
    except Exception as e:
        handler.handle_error(e, {"operation": "object_method_call"})

    # Show error statistics
    stats = handler.get_error_statistics()
    print(f"\nError Statistics: {stats}")

    # Test the decorator
    @handler.wrap_with_error_handling(ErrorCategory.TRANSIENT, {"source": "decorator_test"})
    def risky_function():
        raise TimeoutError("Connection timed out")

    print("\nTesting decorated function...")
    result = risky_function()
    print(f"Function returned: {result}")

    # Test graceful degradation
    @graceful_degradation([ErrorCategory.TRANSIENT, ErrorCategory.DATA])
    def function_with_graceful_degradation():
        raise ValueError("Something went wrong but we can continue")

    print("\nTesting graceful degradation...")
    result = function_with_graceful_degradation()
    print(f"Function with graceful degradation returned: {result}")