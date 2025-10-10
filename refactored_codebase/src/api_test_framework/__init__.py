"""
Enterprise-grade API Testing Framework v2.0

A modern, async-first API testing framework with advanced reporting,
comparison capabilities, and enterprise-ready features.

Key Features:
- Async HTTP client with connection pooling and retry logic
- Pydantic v2 models for data validation and serialization
- Advanced JSON comparison with detailed diff analysis
- Rich HTML reports with charts and analytics
- Flexible configuration management with JSON/environment variables
- Production-ready logging with structured output
- UUID-based run identification replacing magic numbers
- Range-based test data generation
"""

__version__ = "2.0.0"
__author__ = "API Test Framework Team"
__email__ = "team@example.com"
__license__ = "MIT"

# Core imports for easy access
from api_test_framework.core.config import Settings, get_settings
from api_test_framework.core.logging import get_logger, setup_logging

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "Settings",
    "get_settings", 
    "get_logger",
    "setup_logging",
]