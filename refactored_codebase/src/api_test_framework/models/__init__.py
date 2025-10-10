"""
Data models for API Test Framework using Pydantic v2.

This module contains all data models for:
- API request and response structures
- Test execution and results
- Configuration and validation
- Reporting and comparison data

All models use Pydantic v2 features:
- field_validator instead of validator
- model_validator instead of root_validator
- ConfigDict instead of Config class
- Modern type annotations and validation
"""

from api_test_framework.models.base import BaseModel, TimestampedModel
from api_test_framework.models.request_models import (
    APIRequest,
    FullSetRequest,
    PrequalRequest,
    RequestHeader,
    DecisionRequest,
    ApplicationInfo,
    BusinessInfo,
    ApplicantInfo,
)
from api_test_framework.models.response_models import (
    APIResponse,
    ResponseHeader,
    DecisionResponse,
    ErrorResponse,
    ValidationResult,
)
from api_test_framework.models.test_models import (
    TestExecution,
    TestResult,
    TestSuite,
    TestMetrics,
    ComparisonResult,
    ReportData,
)

__all__ = [
    # Base models
    "BaseModel",
    "TimestampedModel",
    
    # Request models
    "APIRequest",
    "FullSetRequest", 
    "PrequalRequest",
    "RequestHeader",
    "DecisionRequest",
    "ApplicationInfo",
    "BusinessInfo",
    "ApplicantInfo",
    
    # Response models
    "APIResponse",
    "ResponseHeader",
    "DecisionResponse", 
    "ErrorResponse",
    "ValidationResult",
    
    # Test models
    "TestExecution",
    "TestResult",
    "TestSuite",
    "TestMetrics",
    "ComparisonResult",
    "ReportData",
]