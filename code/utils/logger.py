"""
Centralized logging utility with structured logging and rotation.

This module provides a singleton logger factory with file rotation,
console output, and structured formatting capabilities.
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from ..core.constants import (
    DEFAULT_ENCODING,
    LOG_BACKUP_COUNT,
    MAX_LOG_FILE_SIZE,
    TIMESTAMP_FORMAT
)


class LoggerFactory:
    """
    Factory for creating and managing application loggers.
    
    Implements singleton pattern to ensure consistent logging across the application.
    """
    
    _instance: Optional["LoggerFactory"] = None
    _loggers: dict[str, logging.Logger] = {}
    
    def __new__(cls) -> "LoggerFactory":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger factory."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.console = Console()
    
    def get_logger(
        self,
        name: str = "APITestFramework",
        log_file: Optional[Path] = None,
        level: str = "INFO",
        log_format: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = True,
        max_bytes: int = MAX_LOG_FILE_SIZE,
        backup_count: int = LOG_BACKUP_COUNT
    ) -> logging.Logger:
        """
        Get or create a configured logger.
        
        Args:
            name: Logger name (used as identifier)
            log_file: Path to log file (if None, auto-generated)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Custom log format string
            enable_console: Whether to enable console output
            enable_file: Whether to enable file output
            max_bytes: Maximum log file size before rotation
            backup_count: Number of backup files to keep
            
        Returns:
            Configured logger instance
        """
        # Return existing logger if already created
        if name in self._loggers:
            return self._loggers[name]
        
        # Create new logger
        logger = logging.getLogger(name)
        logger.setLevel(self._parse_log_level(level))
        logger.handlers.clear()  # Clear any existing handlers
        logger.propagate = False  # Don't propagate to root logger
        
        # Default format
        if log_format is None:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        formatter = logging.Formatter(
            log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Add console handler with Rich formatting
        if enable_console:
            console_handler = RichHandler(
                console=self.console,
                rich_tracebacks=True,
                tracebacks_show_locals=True,
                markup=True
            )
            console_handler.setLevel(logging.INFO)
            logger.addHandler(console_handler)
        
        # Add file handler with rotation
        if enable_file:
            if log_file is None:
                log_file = self._generate_log_file_path(name)
            
            # Ensure log directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=DEFAULT_ENCODING
            )
            file_handler.setLevel(self._parse_log_level(level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Store logger reference
        self._loggers[name] = logger
        
        return logger
    
    def _parse_log_level(self, level: str) -> int:
        """
        Parse log level string to logging constant.
        
        Args:
            level: Log level as string
            
        Returns:
            Logging level constant
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(level.upper(), logging.INFO)
    
    def _generate_log_file_path(self, logger_name: str) -> Path:
        """
        Generate a timestamped log file path.
        
        Args:
            logger_name: Name of the logger
            
        Returns:
            Path to log file
        """
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / f"{logger_name}_{timestamp}.log"
    
    def shutdown(self) -> None:
        """Shutdown all loggers and handlers."""
        for logger in self._loggers.values():
            for handler in logger.handlers:
                handler.close()
                logger.removeHandler(handler)
        self._loggers.clear()


class StructuredLogger:
    """
    Wrapper for logging with structured context.
    
    Provides convenient methods for logging with additional context data.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize structured logger.
        
        Args:
            logger: Base logger instance
        """
        self.logger = logger
    
    def debug(self, message: str, **context) -> None:
        """Log debug message with context."""
        self._log(logging.DEBUG, message, context)
    
    def info(self, message: str, **context) -> None:
        """Log info message with context."""
        self._log(logging.INFO, message, context)
    
    def warning(self, message: str, **context) -> None:
        """Log warning message with context."""
        self._log(logging.WARNING, message, context)
    
    def error(self, message: str, **context) -> None:
        """Log error message with context."""
        self._log(logging.ERROR, message, context)
    
    def critical(self, message: str, **context) -> None:
        """Log critical message with context."""
        self._log(logging.CRITICAL, message, context)
    
    def exception(self, message: str, **context) -> None:
        """Log exception with traceback and context."""
        if context:
            message = f"{message} | Context: {self._format_context(context)}"
        self.logger.exception(message)
    
    def _log(self, level: int, message: str, context: dict) -> None:
        """
        Internal logging method with context formatting.
        
        Args:
            level: Logging level
            message: Log message
            context: Additional context data
        """
        if context:
            message = f"{message} | {self._format_context(context)}"
        self.logger.log(level, message)
    
    def _format_context(self, context: dict) -> str:
        """
        Format context dictionary for logging.
        
        Args:
            context: Context data
            
        Returns:
            Formatted context string
        """
        return " | ".join(f"{k}={v}" for k, v in context.items())


class PerformanceLogger:
    """
    Context manager for logging performance metrics.
    
    Usage:
        with PerformanceLogger(logger, "Operation Name"):
            # perform operation
            pass
    """
    
    def __init__(
        self,
        logger: logging.Logger,
        operation_name: str,
        level: int = logging.INFO
    ):
        """
        Initialize performance logger.
        
        Args:
            logger: Logger instance
            operation_name: Name of the operation being measured
            level: Logging level for performance messages
        """
        self.logger = logger
        self.operation_name = operation_name
        self.level = level
        self.start_time: Optional[float] = None
    
    def __enter__(self) -> "PerformanceLogger":
        """Start performance measurement."""
        import time
        self.start_time = time.time()
        self.logger.log(self.level, f"Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End performance measurement and log duration."""
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.log(
                self.level,
                f"Completed: {self.operation_name} (Duration: {duration:.2f}s)"
            )
        else:
            self.logger.error(
                f"Failed: {self.operation_name} (Duration: {duration:.2f}s) | "
                f"Error: {exc_type.__name__}: {exc_val}"
            )


# Singleton instance
_logger_factory = LoggerFactory()


def get_logger(
    name: str = "APITestFramework",
    log_file: Optional[Path] = None,
    level: str = "INFO",
    **kwargs
) -> logging.Logger:
    """
    Get a configured logger instance.
    
    This is the main entry point for getting loggers throughout the application.
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
        **kwargs: Additional arguments passed to LoggerFactory.get_logger
        
    Returns:
        Configured logger instance
    """
    return _logger_factory.get_logger(name, log_file, level, **kwargs)


def get_structured_logger(
    name: str = "APITestFramework",
    **kwargs
) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        **kwargs: Additional arguments passed to get_logger
        
    Returns:
        Structured logger instance
    """
    logger = get_logger(name, **kwargs)
    return StructuredLogger(logger)


def shutdown_logging() -> None:
    """Shutdown all loggers and handlers."""
    _logger_factory.shutdown()


# Example usage and testing
if __name__ == "__main__":
    # Basic logger
    logger = get_logger("TestLogger")
    logger.info("This is an info message")
    logger.error("This is an error message")
    
    # Structured logger
    struct_logger = get_structured_logger("StructuredLogger")
    struct_logger.info("Processing file", file_name="test.json", size=1024)
    struct_logger.error("Failed to process", error_code=500, reason="Server error")
    
    # Performance logger
    import time
    with PerformanceLogger(logger, "Expensive Operation"):
        time.sleep(1)  # Simulate work
    
    # Cleanup
    shutdown_logging()