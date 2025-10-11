"""
API Testing Framework - Enterprise-grade automated API testing solution.

This framework provides comprehensive tools for:
- Test data preparation with APPID generation
- Parallel asynchronous API testing
- Deep JSON comparison
- Multi-format report generation (HTML, JSON, Excel)
- Configuration-driven execution

Author: Refactored with modern Python best practices
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "API Testing Framework Team"

from apitesting.config import load_config, get_config
from apitesting.services import (
    TestDataService,
    HTTPService,
    ComparisonService,
    ReportService
)

__all__ = [
    "__version__",
    "__author__",
    "load_config",
    "get_config",
    "TestDataService",
    "HTTPService",
    "ComparisonService",
    "ReportService"
]