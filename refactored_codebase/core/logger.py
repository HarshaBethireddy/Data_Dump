"""
Enterprise-grade logging system with structured logging and multiple handlers.

Provides centralized, configurable logging with support for different
output formats, log levels, and destinations.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """Enumeration of log levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormatter(logging.Formatter):
    """Custom formatter with enhanced formatting capabilities."""
    
    def __init__(self, include_thread: bool = False, include_process: bool = False):
        """
        Initialize custom formatter.
        
        Args:
            include_thread: Include thread information in logs
            include_process: Include process information in logs
        """
        self.include_thread = include_thread
        self.include_process = include_process
        
        # Base format
        fmt_parts = [
            '%(asctime)s',
            '%(name)s',
            '%(levelname)s'
        ]
        
        if include_process:
            fmt_parts.append('PID:%(process)d')
        
        if include_thread:
            fmt_parts.append('TID:%(thread)d')
        
        fmt_parts.append('%(message)s')
        
        format_string = ' - '.join(fmt_parts)
        super().__init__(format_string, datefmt='%Y-%m-%d %H:%M:%S')


class FrameworkLogger:
    """
    Enterprise-grade logger with multiple handlers and structured logging.
    
    Supports file logging, console logging, and structured output with
    configurable levels and formatting.
    """
    
    def __init__(self, name: str = "APITestFramework"):
        """
        Initialize framework logger.
        
        Args:
            name: Logger name
        """
        self.name = name
        self._logger: Optional[logging.Logger] = None
        self._handlers: Dict[str, logging.Handler] = {}
        
    def setup(self, 
              log_file: Optional[Union[str, Path]] = None,
              console_level: LogLevel = LogLevel.INFO,
              file_level: LogLevel = LogLevel.DEBUG,
              max_file_size: int = 10 * 1024 * 1024,  # 10MB
              backup_count: int = 5,
              include_thread_info: bool = False) -> logging.Logger:
        """
        Setup and configure the logger with multiple handlers.
        
        Args:
            log_file: Path to log file (optional)
            console_level: Console logging level
            file_level: File logging level
            max_file_size: Maximum log file size before rotation
            backup_count: Number of backup files to keep
            include_thread_info: Include thread information in logs
            
        Returns:
            Configured logger instance
        """
        if self._logger is not None:
            return self._logger
        
        # Create logger
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers will filter
        
        # Clear any existing handlers
        self._logger.handlers.clear()
        
        # Setup console handler
        self._setup_console_handler(console_level, include_thread_info)
        
        # Setup file handler if log file specified
        if log_file:
            self._setup_file_handler(
                log_file, file_level, max_file_size, 
                backup_count, include_thread_info
            )
        
        # Prevent propagation to root logger
        self._logger.propagate = False
        
        return self._logger
    
    def _setup_console_handler(self, level: LogLevel, include_thread_info: bool) -> None:
        """Setup console logging handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level.value)
        
        # Use colored formatter for console if available
        formatter = LogFormatter(include_thread=include_thread_info)
        console_handler.setFormatter(formatter)
        
        self._logger.addHandler(console_handler)
        self._handlers['console'] = console_handler
    
    def _setup_file_handler(self, 
                           log_file: Union[str, Path],
                           level: LogLevel,
                           max_file_size: int,
                           backup_count: int,
                           include_thread_info: bool) -> None:
        """Setup rotating file logging handler."""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler to prevent huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level.value)
        
        # More detailed formatter for file logs
        formatter = LogFormatter(
            include_thread=include_thread_info,
            include_process=True
        )
        file_handler.setFormatter(formatter)
        
        self._logger.addHandler(file_handler)
        self._handlers['file'] = file_handler
    
    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance.
        
        Returns:
            Logger instance
            
        Raises:
            RuntimeError: If logger not initialized
        """
        if self._logger is None:
            raise RuntimeError("Logger not initialized. Call setup() first.")
        return self._logger
    
    def add_handler(self, name: str, handler: logging.Handler) -> None:
        """
        Add a custom handler to the logger.
        
        Args:
            name: Handler name for reference
            handler: Logging handler instance
        """
        if self._logger is None:
            raise RuntimeError("Logger not initialized. Call setup() first.")
        
        self._logger.addHandler(handler)
        self._handlers[name] = handler
    
    def remove_handler(self, name: str) -> None:
        """
        Remove a handler from the logger.
        
        Args:
            name: Handler name to remove
        """
        if name in self._handlers:
            self._logger.removeHandler(self._handlers[name])
            del self._handlers[name]
    
    def set_level(self, level: LogLevel) -> None:
        """
        Set the logging level for all handlers.
        
        Args:
            level: New logging level
        """
        if self._logger is None:
            raise RuntimeError("Logger not initialized. Call setup() first.")
        
        for handler in self._handlers.values():
            handler.setLevel(level.value)
    
    def log_structured(self, level: LogLevel, message: str, **kwargs) -> None:
        """
        Log a structured message with additional context.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional context data
        """
        if self._logger is None:
            raise RuntimeError("Logger not initialized. Call setup() first.")
        
        # Format structured data
        if kwargs:
            context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            full_message = f"{message} | {context}"
        else:
            full_message = message
        
        self._logger.log(level.value, full_message)
    
    def close(self) -> None:
        """Close all handlers and cleanup resources."""
        if self._logger is None:
            return
        
        for handler in list(self._handlers.values()):
            handler.close()
            self._logger.removeHandler(handler)
        
        self._handlers.clear()
        self._logger = None


class LoggerFactory:
    """Factory for creating configured logger instances."""
    
    _instances: Dict[str, FrameworkLogger] = {}
    
    @classmethod
    def get_logger(cls, 
                   name: str,
                   log_file: Optional[Union[str, Path]] = None,
                   console_level: LogLevel = LogLevel.INFO,
                   file_level: LogLevel = LogLevel.DEBUG) -> logging.Logger:
        """
        Get or create a logger instance.
        
        Args:
            name: Logger name
            log_file: Optional log file path
            console_level: Console logging level
            file_level: File logging level
            
        Returns:
            Configured logger instance
        """
        if name not in cls._instances:
            framework_logger = FrameworkLogger(name)
            framework_logger.setup(
                log_file=log_file,
                console_level=console_level,
                file_level=file_level
            )
            cls._instances[name] = framework_logger
        
        return cls._instances[name].get_logger()
    
    @classmethod
    def cleanup_all(cls) -> None:
        """Cleanup all logger instances."""
        for logger in cls._instances.values():
            logger.close()
        cls._instances.clear()


# Default logger instance for backward compatibility
default_logger = FrameworkLogger()