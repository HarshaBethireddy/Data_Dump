"""
Services package initialization.

Provides convenient imports for all service classes.
"""

from ..services.test_data_service import (
    AppIDGenerator,
    TestDataProcessor,
    TestDataService
)

from ..services.http_service import (
    AsyncHTTPClient,
    HTTPService
)

from ..services.comparison_service import (
    JSONComparator,
    ComparisonService
)

from ..services.report_service import (
    StatisticsCalculator,
    HTMLReportGenerator,
    ReportService
)

__all__ = [
    # Test Data Service
    "AppIDGenerator",
    "TestDataProcessor",
    "TestDataService",
    
    # HTTP Service
    "AsyncHTTPClient",
    "HTTPService",
    
    # Comparison Service
    "JSONComparator",
    "ComparisonService",
    
    # Report Service
    "StatisticsCalculator",
    "HTMLReportGenerator",
    "ReportService"
]