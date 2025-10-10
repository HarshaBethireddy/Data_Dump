"""
Core module for API Test Framework.

This module contains the foundational components:
- Configuration management with Pydantic v2
- Custom exception hierarchy
- Structured logging setup
- Base utilities and constants
"""

from api_test_framework.core.config import Settings, get_settings
from api_test_framework.core.exceptions import (
    APITestFrameworkError,
    ConfigurationError,
    ValidationError,
    HTTPClientError,
    TestDataError,
    ComparisonError,
    ReportGenerationError,
)
from api_test_framework.core.logging import get_logger, setup_logging

__all__ = [
    # Configuration
    "Settings",
    "get_settings",
    
    # Exceptions
    "APITestFrameworkError",
    "ConfigurationError", 
    "ValidationError",
    "HTTPClientError",
    "TestDataError",
    "ComparisonError",
    "ReportGenerationError",
    
    # Logging
    "get_logger",
    "setup_logging",
]