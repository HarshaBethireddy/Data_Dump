"""
Centralized logging configuration for the API testing framework.
"""
import logging
import os
from datetime import datetime
from typing import Optional


class FrameworkLogger:
    """Centralized logger for the framework."""
    
    def __init__(self, name: str = "APITestFramework"):
        self.name = name
        self._logger: Optional[logging.Logger] = None
    
    def setup_logger(self, log_file: str, level: int = logging.INFO) -> logging.Logger:
        """Setup and configure logger."""
        if self._logger is not None:
            return self._logger
        
        # Create logger
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(level)
        
        # Clear any existing handlers
        self._logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        return self._logger
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger."""
        if self._logger is None:
            raise RuntimeError("Logger not initialized. Call setup_logger first.")
        return self._logger


# Global logger instance
framework_logger = FrameworkLogger()