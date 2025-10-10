"""
Custom exception classes for the API testing framework.

This module defines domain-specific exceptions that provide clear error
context and enable proper error handling throughout the application.
"""

from typing import Optional, Any, Dict


class APITestFrameworkError(Exception):
    """Base exception for all framework-related errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize the base exception.
        
        Args:
            message: Human-readable error message
            details: Additional error context as dictionary
            original_error: Original exception that caused this error
        """
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        error_str = self.message
        if self.details:
            error_str += f" | Details: {self.details}"
        if self.original_error:
            error_str += f" | Caused by: {type(self.original_error).__name__}: {str(self.original_error)}"
        return error_str


class ConfigurationError(APITestFrameworkError):
    """Raised when there's an issue with configuration."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: The configuration key that caused the error
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details=details, **kwargs)


class ValidationError(APITestFrameworkError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Validation error",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: The field that failed validation
            value: The invalid value
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, details=details, **kwargs)


class FileOperationError(APITestFrameworkError):
    """Raised when file operations fail."""
    
    def __init__(
        self,
        message: str = "File operation error",
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize file operation error.
        
        Args:
            message: Error message
            file_path: Path to the file that caused the error
            operation: The operation that failed (read, write, delete, etc.)
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        super().__init__(message, details=details, **kwargs)


class JSONProcessingError(APITestFrameworkError):
    """Raised when JSON processing fails."""
    
    def __init__(
        self,
        message: str = "JSON processing error",
        file_path: Optional[str] = None,
        json_path: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize JSON processing error.
        
        Args:
            message: Error message
            file_path: Path to the JSON file
            json_path: Path within the JSON structure (e.g., 'data.user.id')
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path
        if json_path:
            details["json_path"] = json_path
        super().__init__(message, details=details, **kwargs)


class ExcelProcessingError(APITestFrameworkError):
    """Raised when Excel file processing fails."""
    
    def __init__(
        self,
        message: str = "Excel processing error",
        file_path: Optional[str] = None,
        sheet_name: Optional[str] = None,
        row: Optional[int] = None,
        column: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize Excel processing error.
        
        Args:
            message: Error message
            file_path: Path to the Excel file
            sheet_name: Name of the sheet
            row: Row number where error occurred
            column: Column number where error occurred
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path
        if sheet_name:
            details["sheet_name"] = sheet_name
        if row is not None:
            details["row"] = row
        if column is not None:
            details["column"] = column
        super().__init__(message, details=details, **kwargs)


class HTTPRequestError(APITestFrameworkError):
    """Raised when HTTP requests fail."""
    
    def __init__(
        self,
        message: str = "HTTP request error",
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        method: str = "POST",
        **kwargs
    ):
        """
        Initialize HTTP request error.
        
        Args:
            message: Error message
            url: The URL that was requested
            status_code: HTTP status code received
            method: HTTP method used
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if url:
            details["url"] = url
        if status_code is not None:
            details["status_code"] = status_code
        details["method"] = method
        super().__init__(message, details=details, **kwargs)


class TestDataPreparationError(APITestFrameworkError):
    """Raised when test data preparation fails."""
    
    def __init__(
        self,
        message: str = "Test data preparation error",
        data_type: Optional[str] = None,
        step: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize test data preparation error.
        
        Args:
            message: Error message
            data_type: Type of test data (regular, prequal)
            step: The preparation step that failed
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if data_type:
            details["data_type"] = data_type
        if step:
            details["step"] = step
        super().__init__(message, details=details, **kwargs)


class ComparisonError(APITestFrameworkError):
    """Raised when comparison operations fail."""
    
    def __init__(
        self,
        message: str = "Comparison error",
        file1: Optional[str] = None,
        file2: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize comparison error.
        
        Args:
            message: Error message
            file1: First file being compared
            file2: Second file being compared
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if file1:
            details["file1"] = file1
        if file2:
            details["file2"] = file2
        super().__init__(message, details=details, **kwargs)


class ReportGenerationError(APITestFrameworkError):
    """Raised when report generation fails."""
    
    def __init__(
        self,
        message: str = "Report generation error",
        report_type: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize report generation error.
        
        Args:
            message: Error message
            report_type: Type of report (HTML, JSON, Excel)
            output_path: Path where report should be generated
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if report_type:
            details["report_type"] = report_type
        if output_path:
            details["output_path"] = output_path
        super().__init__(message, details=details, **kwargs)


class AppIDGenerationError(APITestFrameworkError):
    """Raised when APPID generation fails."""
    
    def __init__(
        self,
        message: str = "APPID generation error",
        start_value: Optional[Any] = None,
        increment: Optional[int] = None,
        count: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize APPID generation error.
        
        Args:
            message: Error message
            start_value: Starting APPID value
            increment: Increment value
            count: Number of IDs to generate
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if start_value is not None:
            details["start_value"] = str(start_value)
        if increment is not None:
            details["increment"] = increment
        if count is not None:
            details["count"] = count
        super().__init__(message, details=details, **kwargs)


class ResourceNotFoundError(APITestFrameworkError):
    """Raised when a required resource is not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_path: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize resource not found error.
        
        Args:
            message: Error message
            resource_type: Type of resource (file, folder, template, etc.)
            resource_path: Path to the resource
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_path:
            details["resource_path"] = resource_path
        super().__init__(message, details=details, **kwargs)


class ParallelExecutionError(APITestFrameworkError):
    """Raised when parallel execution encounters issues."""
    
    def __init__(
        self,
        message: str = "Parallel execution error",
        worker_count: Optional[int] = None,
        failed_tasks: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize parallel execution error.
        
        Args:
            message: Error message
            worker_count: Number of parallel workers
            failed_tasks: Number of tasks that failed
            **kwargs: Additional arguments passed to base class
        """
        details = kwargs.pop("details", {})
        if worker_count is not None:
            details["worker_count"] = worker_count
        if failed_tasks is not None:
            details["failed_tasks"] = failed_tasks
        super().__init__(message, details=details, **kwargs)