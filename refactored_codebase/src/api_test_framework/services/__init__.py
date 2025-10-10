"""
Services module for API Test Framework.

This module contains all business logic services:
- Async HTTP client with advanced retry logic and connection pooling
- Test data service with range-based ID generation
- Comparison service with deep JSON diff analysis
- Report service with interactive charts and analytics

All services are designed for maximum performance with minimal code.
"""

from api_test_framework.services.http_client import HTTPClientService
from api_test_framework.services.test_data_service import TestDataService
from api_test_framework.services.comparison_service import ComparisonService
from api_test_framework.services.report_service import ReportService

__all__ = [
    "HTTPClientService",
    "TestDataService", 
    "ComparisonService",
    "ReportService",
]