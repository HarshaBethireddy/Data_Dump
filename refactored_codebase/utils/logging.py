"""
Enterprise logging system with structured logging and multiple outputs.

This module provides a centralized logging system with support for:
- Structured logging with context
- Multiple output formats (console, file, JSON)
- Log rotation and archival
- Performance monitoring
- Request tracing
"""

import logging
import logging.handlers
import sys
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from refactored_codebase.config.models import LoggingConfig


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'elapsed_time'):
            log_entry['elapsed_time'] = record.elapsed_time
        
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """Filter to add context information to log records."""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Initialize context filter.
        
        Args:
            context: Additional context to add to all log records
        """
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class LoggerManager:
    """Centralized logger manager."""
    
    _instance = None
    _loggers: Dict[str, logging.Logger] = {}
    _configured = False
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def setup_logging(self, config: LoggingConfig, log_dir: Path) -> None:
        """
        Setup logging configuration.
        
        Args:
            config: Logging configuration
            log_dir: Directory for log files
        """
        if self._configured:
            return
        
        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.level.value))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = log_dir / "framework.log"
        if config.file_rotation:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self._parse_file_size(config.max_file_size),
                backupCount=config.backup_count,
                encoding='utf-8'
            )
        else:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        file_handler.setLevel(getattr(logging, config.level.value))
        file_formatter = logging.Formatter(
            config.format,
            datefmt=config.date_format
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # JSON log handler for structured logging
        json_log_file = log_dir / "framework.json.log"
        json_handler = logging.FileHandler(json_log_file, encoding='utf-8')
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
        
        self._configured = True
    
    def _parse_file_size(self, size_str: str) -> int:
        """Parse file size string to bytes."""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def get_logger(self, name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """
        Get logger instance with optional context.
        
        Args:
            name: Logger name
            context: Additional context for all log messages
            
        Returns:
            Configured logger instance
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            
            # Add context filter if provided
            if context:
                context_filter = ContextFilter(context)
                logger.addFilter(context_filter)
            
            self._loggers[name] = logger
        
        return self._loggers[name]


# Global logger manager instance
_logger_manager = LoggerManager()


def setup_logging(config: LoggingConfig, log_dir: Path) -> None:
    """
    Setup logging configuration.
    
    Args:
        config: Logging configuration
        log_dir: Directory for log files
    """
    _logger_manager.setup_logging(config, log_dir)


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get logger instance.
    
    Args:
        name: Logger name (typically __name__ or class name)
        context: Additional context for all log messages
        
    Returns:
        Configured logger instance
    """
    return _logger_manager.get_logger(name, context)


class LogContext:
    """Context manager for adding temporary context to logs."""
    
    def __init__(self, logger: logging.Logger, **context):
        """
        Initialize log context.
        
        Args:
            logger: Logger instance
            **context: Context key-value pairs
        """
        self.logger = logger
        self.context = context
        self.filter = None
    
    def __enter__(self):
        """Enter context manager."""
        self.filter = ContextFilter(self.context)
        self.logger.addFilter(self.filter)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.filter:
            self.logger.removeFilter(self.filter)


def log_performance(func):
    """Decorator to log function performance."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.debug(
                f"Function {func.__name__} completed in {elapsed:.3f}s",
                extra={"function": func.__name__, "elapsed_time": elapsed}
            )
            return result
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Function {func.__name__} failed after {elapsed:.3f}s: {e}",
                extra={"function": func.__name__, "elapsed_time": elapsed, "error": str(e)}
            )
            raise
    
    return wrapper