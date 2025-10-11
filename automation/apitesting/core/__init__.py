"""
Core package initialization.

Provides convenient imports for core models, constants, and exceptions.
"""

from apitesting.core.constants import (
    TestDataType,
    HTTPStatusCategory,
    FileExtension,
    LogLevel,
    TIMESTAMP_FORMAT,
    APPID_PLACEHOLDER,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_PARALLEL_WORKERS
)

from apitesting.core.exceptions import (
    APITestFrameworkError,
    ConfigurationError,
    ValidationError,
    FileOperationError,
    JSONProcessingError,
    ExcelProcessingError,
    HTTPRequestError,
    TestDataPreparationError,
    ComparisonError,
    ReportGenerationError,
    AppIDGenerationError,
    ResourceNotFoundError,
    ParallelExecutionError
)

from apitesting.core.models import (
    # Configuration Models
    APIConfig,
    TestExecutionConfig,
    TestDataConfig,
    PathsConfig,
    LoggingConfig,
    ReportsConfig,
    ApplicationConfig,
    # Request/Response Models
    RequestResult,
    BatchRequestResult,
    # Test Data Models
    AppIDRange,
    TestDataFile,
    # Comparison Models
    JSONDifference,
    FileComparisonResult,
    ComparisonSummary,
    # Report Models
    StatusCodeDistribution,
    TestStatistics,
    TestReport,
    # Merge Models
    MergeResult,
    MergeSummary,
    # Enums
    TestDataType as TestDataTypeEnum,
    ReportFormat,
    ExecutionStatus
)

__all__ = [
    # Constants
    "TestDataType",
    "HTTPStatusCategory",
    "FileExtension",
    "LogLevel",
    "TIMESTAMP_FORMAT",
    "APPID_PLACEHOLDER",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_PARALLEL_WORKERS",
    
    # Exceptions
    "APITestFrameworkError",
    "ConfigurationError",
    "ValidationError",
    "FileOperationError",
    "JSONProcessingError",
    "ExcelProcessingError",
    "HTTPRequestError",
    "TestDataPreparationError",
    "ComparisonError",
    "ReportGenerationError",
    "AppIDGenerationError",
    "ResourceNotFoundError",
    "ParallelExecutionError",
    
    # Models
    "APIConfig",
    "TestExecutionConfig",
    "TestDataConfig",
    "PathsConfig",
    "LoggingConfig",
    "ReportsConfig",
    "ApplicationConfig",
    "RequestResult",
    "BatchRequestResult",
    "AppIDRange",
    "TestDataFile",
    "JSONDifference",
    "FileComparisonResult",
    "ComparisonSummary",
    "StatusCodeDistribution",
    "TestStatistics",
    "TestReport",
    "MergeResult",
    "MergeSummary",
    "TestDataTypeEnum",
    "ReportFormat",
    "ExecutionStatus"
]