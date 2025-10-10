"""
Enterprise-grade structured logging configuration for API Test Framework.

Features:
- Structured logging with JSON output for production
- Rich console output for development
- Multiple log levels and handlers
- Async-safe logging
- Performance metrics logging
- Request/response correlation IDs
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

import structlog
from rich.console import Console
from rich.logging import RichHandler


class StructuredLogger:
    """Structured logger with rich formatting and JSON output."""
    
    def __init__(self, name: str = "api_test_framework"):
        self.name = name
        self._logger: Optional[structlog.BoundLogger] = None
        self._console = Console()
    
    def setup(
        self,
        log_level: Union[str, int] = logging.INFO,
        log_file: Optional[Path] = None,
        enable_json_logs: bool = False,
        enable_console_logs: bool = True,
    ) -> structlog.BoundLogger:
        """Setup structured logging with multiple handlers."""
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.CallsiteParameterAdder(
                    parameters=[
                        structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                    ]
                ),
                self._add_correlation_id,
                structlog.processors.JSONRenderer() if enable_json_logs 
                else structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.getLevelName(log_level) if isinstance(log_level, int) else log_level
            ),
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Setup standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=log_level,
            handlers=[]
        )
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Add console handler if enabled
        if enable_console_logs:
            console_handler = RichHandler(
                console=self._console,
                show_time=True,
                show_path=True,
                markup=True,
                rich_tracebacks=True,
            )
            console_handler.setLevel(log_level)
            root_logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            
            if enable_json_logs:
                file_formatter = logging.Formatter('%(message)s')
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        
        # Create structured logger
        self._logger = structlog.get_logger(self.name)
        return self._logger
    
    def get_logger(self) -> structlog.BoundLogger:
        """Get the configured structured logger."""
        if self._logger is None:
            raise RuntimeError("Logger not initialized. Call setup() first.")
        return self._logger
    
    @staticmethod
    def _add_correlation_id(
        logger: logging.Logger, 
        method_name: str, 
        event_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add correlation ID to log events."""
        # Try to get correlation ID from context
        correlation_id = structlog.contextvars.get_contextvars().get("correlation_id")
        if correlation_id:
            event_dict["correlation_id"] = correlation_id
        return event_dict


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def setup_logging(
    log_level: Union[str, int] = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    enable_json_logs: bool = False,
    enable_console_logs: bool = True,
    logger_name: str = "api_test_framework",
) -> structlog.BoundLogger:
    """Setup global logging configuration."""
    global _global_logger
    
    _global_logger = StructuredLogger(logger_name)
    
    log_file_path = Path(log_file) if log_file else None
    
    return _global_logger.setup(
        log_level=log_level,
        log_file=log_file_path,
        enable_json_logs=enable_json_logs,
        enable_console_logs=enable_console_logs,
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a logger instance with optional name binding."""
    if _global_logger is None:
        # Auto-setup with defaults if not configured
        setup_logging()
    
    logger = _global_logger.get_logger()
    
    if name:
        return logger.bind(component=name)
    
    return logger


def bind_correlation_id(correlation_id: str) -> None:
    """Bind correlation ID to current context for request tracing."""
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def clear_correlation_id() -> None:
    """Clear correlation ID from current context."""
    structlog.contextvars.clear_contextvars()


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger bound to this class."""
        return get_logger(self.__class__.__name__)


# Performance logging utilities
class PerformanceLogger:
    """Utility for logging performance metrics."""
    
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or get_logger("performance")
    
    def log_request_metrics(
        self,
        method: str,
        url: str,
        status_code: int,
        response_time: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        **kwargs
    ) -> None:
        """Log HTTP request performance metrics."""
        self.logger.info(
            "HTTP request completed",
            method=method,
            url=url,
            status_code=status_code,
            response_time_ms=round(response_time * 1000, 2),
            request_size_bytes=request_size,
            response_size_bytes=response_size,
            **kwargs
        )
    
    def log_operation_metrics(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        **kwargs
    ) -> None:
        """Log general operation performance metrics."""
        self.logger.info(
            "Operation completed",
            operation=operation,
            duration_ms=round(duration * 1000, 2),
            success=success,
            **kwargs
        )