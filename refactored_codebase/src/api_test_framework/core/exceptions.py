"""
Custom exception hierarchy for API Test Framework.

Provides structured error handling with specific exception types
for different components and operations.
"""

from typing import Any, Dict, Optional


class APITestFrameworkError(Exception):
    """Base exception for all API Test Framework errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None,
        }


class ConfigurationError(APITestFrameworkError):
    """Raised when configuration is invalid or missing."""
    pass


class ValidationError(APITestFrameworkError):
    """Raised when data validation fails."""
    pass


class HTTPClientError(APITestFrameworkError):
    """Raised when HTTP client operations fail."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        url: Optional[str] = None,
        **kwargs
    ) -> None:
        details = {
            "status_code": status_code,
            "response_body": response_body,
            "url": url,
            **kwargs
        }
        super().__init__(message, details)
        self.status_code = status_code
        self.response_body = response_body
        self.url = url


class TestDataError(APITestFrameworkError):
    """Raised when test data processing fails."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        data_type: Optional[str] = None,
        **kwargs
    ) -> None:
        details = {
            "file_path": file_path,
            "data_type": data_type,
            **kwargs
        }
        super().__init__(message, details)
        self.file_path = file_path
        self.data_type = data_type


class ComparisonError(APITestFrameworkError):
    """Raised when JSON comparison operations fail."""
    
    def __init__(
        self,
        message: str,
        comparison_type: Optional[str] = None,
        source_file: Optional[str] = None,
        target_file: Optional[str] = None,
        **kwargs
    ) -> None:
        details = {
            "comparison_type": comparison_type,
            "source_file": source_file,
            "target_file": target_file,
            **kwargs
        }
        super().__init__(message, details)
        self.comparison_type = comparison_type
        self.source_file = source_file
        self.target_file = target_file


class ReportGenerationError(APITestFrameworkError):
    """Raised when report generation fails."""
    
    def __init__(
        self,
        message: str,
        report_type: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> None:
        details = {
            "report_type": report_type,
            "output_path": output_path,
            **kwargs
        }
        super().__init__(message, details)
        self.report_type = report_type
        self.output_path = output_path


class FileOperationError(APITestFrameworkError):
    """Raised when file operations fail."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ) -> None:
        details = {
            "file_path": file_path,
            "operation": operation,
            **kwargs
        }
        super().__init__(message, details)
        self.file_path = file_path
        self.operation = operation


class IDGenerationError(APITestFrameworkError):
    """Raised when ID generation fails."""
    
    def __init__(
        self,
        message: str,
        id_type: Optional[str] = None,
        range_start: Optional[int] = None,
        range_end: Optional[int] = None,
        **kwargs
    ) -> None:
        details = {
            "id_type": id_type,
            "range_start": range_start,
            "range_end": range_end,
            **kwargs
        }
        super().__init__(message, details)
        self.id_type = id_type
        self.range_start = range_start
        self.range_end = range_end