"""
Application-wide constants and enumerations.

This module defines all constant values used across the application,
promoting consistency and making maintenance easier.
"""

from enum import Enum
from typing import Final


class TestDataType(str, Enum):
    """Types of test data that can be processed."""
    
    REGULAR = "regular"
    PREQUAL = "prequal"
    BOTH = "both"


class HTTPStatusCategory(str, Enum):
    """HTTP status code categories."""
    
    SUCCESS = "2xx"
    REDIRECTION = "3xx"
    CLIENT_ERROR = "4xx"
    SERVER_ERROR = "5xx"


class FileExtension(str, Enum):
    """Supported file extensions."""
    
    JSON = ".json"
    CSV = ".csv"
    XLSX = ".xlsx"
    HTML = ".html"
    TXT = ".txt"
    LOG = ".log"


class LogLevel(str, Enum):
    """Logging levels."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# File and folder naming patterns
TIMESTAMP_FORMAT: Final[str] = "%Y%m%d_%H%M%S"
RESPONSE_FILE_SUFFIX: Final[str] = "_response"
COMPARISON_FILE_SUFFIX: Final[str] = "_comparison_result"
SUMMARY_FILE_NAME: Final[str] = "summary"

# JSON placeholder for APPID
APPID_PLACEHOLDER: Final[str] = "$APPID"

# HTTP configuration defaults
DEFAULT_TIMEOUT: Final[int] = 30
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_DELAY: Final[float] = 1.0
DEFAULT_PARALLEL_WORKERS: Final[int] = 10

# APPID configuration
PREQUAL_APPID_LENGTH: Final[int] = 20
REGULAR_APPID_MIN: Final[int] = 1000000
REGULAR_APPID_MAX: Final[int] = 9999999999

# Report configuration
HTML_REPORT_NAME: Final[str] = "test_report.html"
JSON_REPORT_NAME: Final[str] = "test_report.json"
EXCEL_REPORT_NAME: Final[str] = "test_report.xlsx"
COMPARISON_SUMMARY_NAME: Final[str] = "comparison_summary.txt"
MERGE_SUMMARY_NAME: Final[str] = "merge_summary.txt"

# Excel configuration
EXCEL_APPID_COLUMN: Final[int] = 1  # Column A
EXCEL_DATA_START_ROW: Final[int] = 2  # Row 2 (after header)

# Error messages
ERROR_FILE_NOT_FOUND: Final[str] = "File not found: {path}"
ERROR_INVALID_JSON: Final[str] = "Invalid JSON in file: {path}"
ERROR_INVALID_CONFIG: Final[str] = "Invalid configuration: {detail}"
ERROR_API_REQUEST_FAILED: Final[str] = "API request failed: {detail}"
ERROR_COMPARISON_FAILED: Final[str] = "Comparison failed: {detail}"

# Success messages
SUCCESS_TEST_COMPLETED: Final[str] = "Test execution completed successfully"
SUCCESS_COMPARISON_COMPLETED: Final[str] = "Comparison completed successfully"
SUCCESS_REPORT_GENERATED: Final[str] = "Report generated: {path}"

# Encoding
DEFAULT_ENCODING: Final[str] = "utf-8"
FALLBACK_ENCODINGS: Final[tuple] = ("utf-8-sig", "iso-8859-1", "cp1252", "latin1")

# HTTP Status Codes (commonly used)
HTTP_OK: Final[int] = 200
HTTP_CREATED: Final[int] = 201
HTTP_BAD_REQUEST: Final[int] = 400
HTTP_UNAUTHORIZED: Final[int] = 401
HTTP_FORBIDDEN: Final[int] = 403
HTTP_NOT_FOUND: Final[int] = 404
HTTP_INTERNAL_ERROR: Final[int] = 500
HTTP_SERVICE_UNAVAILABLE: Final[int] = 503

# Retry status codes (when to retry requests)
RETRY_STATUS_CODES: Final[tuple] = (429, 500, 502, 503, 504)

# Response analysis keywords
ERROR_KEYWORDS: Final[tuple] = (
    "error",
    "Error",
    "ERROR",
    "fail",
    "Fail",
    "FAIL",
    "exception",
    "Exception",
    "EXCEPTION"
)

# File patterns
JSON_FILE_PATTERN: Final[str] = "*.json"
CSV_FILE_PATTERN: Final[str] = "*.csv"
XLSX_FILE_PATTERN: Final[str] = "*.xlsx"

# Report styling
REPORT_PRIMARY_COLOR: Final[str] = "#667eea"
REPORT_SUCCESS_COLOR: Final[str] = "#4CAF50"
REPORT_ERROR_COLOR: Final[str] = "#f44336"
REPORT_WARNING_COLOR: Final[str] = "#ff9800"

# Comparison result values
COMPARISON_NULL_VALUE: Final[str] = "NULL"
COMPARISON_EMPTY_VALUE: Final[str] = "EMPTY"
COMPARISON_VALID_JSON: Final[str] = "VALID_JSON"
COMPARISON_INVALID_JSON: Final[str] = "INVALID_JSON"
COMPARISON_ERROR: Final[str] = "COMPARISON_ERROR"

# Excel formatting
EXCEL_HEADER_COLOR: Final[str] = "4472C4"
EXCEL_SEPARATOR_COLOR: Final[str] = "FFFF00"
EXCEL_MAX_COLUMN_WIDTH: Final[int] = 50
EXCEL_MIN_COLUMN_WIDTH: Final[int] = 10

# CSV configuration
CSV_DELIMITER: Final[str] = ","
CSV_QUOTECHAR: Final[str] = '"'

# Performance settings
MAX_RESPONSE_PREVIEW_LENGTH: Final[int] = 200
MAX_ERROR_MESSAGE_LENGTH: Final[int] = 500
MAX_LOG_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT: Final[int] = 5