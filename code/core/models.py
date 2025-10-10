"""
Pydantic V2 data models for the API testing framework.

This module defines all data structures used throughout the application,
providing validation, serialization, and type safety.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
    HttpUrl
)


class TestDataType(str, Enum):
    """Types of test data."""
    
    REGULAR = "regular"
    PREQUAL = "prequal"
    BOTH = "both"


class ReportFormat(str, Enum):
    """Report output formats."""
    
    HTML = "html"
    JSON = "json"
    EXCEL = "excel"


class ExecutionStatus(str, Enum):
    """Test execution status."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


# ============================================================================
# Configuration Models
# ============================================================================

class APIConfig(BaseModel):
    """API configuration settings."""
    
    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True
    )
    
    url: HttpUrl = Field(..., description="API endpoint URL")
    host: str = Field(..., description="API host header value")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Whether to verify SSL certificates")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.0, le=60.0, description="Delay between retries in seconds")


class TestExecutionConfig(BaseModel):
    """Test execution configuration."""
    
    model_config = ConfigDict(
        frozen=True
    )
    
    parallel_workers: int = Field(default=10, ge=1, le=100, description="Number of parallel workers")
    think_time: float = Field(default=0.0, ge=0.0, le=60.0, description="Think time between requests in seconds")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Batch size for processing")


class TestDataConfig(BaseModel):
    """Test data configuration."""
    
    model_config = ConfigDict(frozen=True)
    
    appid_start: int = Field(default=1000000, ge=1, description="Starting APPID for regular tests")
    appid_increment: int = Field(default=1, ge=1, description="APPID increment value")
    prequal_appid_start: str = Field(
        default="10000000000000000000",
        description="Starting APPID for prequal tests (20 digits)"
    )
    prequal_appid_increment: int = Field(default=1, ge=1, description="Prequal APPID increment")
    
    @field_validator("prequal_appid_start")
    @classmethod
    def validate_prequal_appid(cls, v: str) -> str:
        """Validate prequal APPID format."""
        if not v.isdigit():
            raise ValueError("Prequal APPID must contain only digits")
        if len(v) != 20:
            raise ValueError("Prequal APPID must be exactly 20 digits")
        return v


class PathsConfig(BaseModel):
    """File system paths configuration."""
    
    model_config = ConfigDict(frozen=True)
    
    input_templates_regular: Path = Field(..., description="Path to regular JSON templates")
    input_templates_prequal: Path = Field(..., description="Path to prequal JSON templates")
    input_test_data_regular: Path = Field(..., description="Path to regular test data Excel file")
    input_test_data_prequal: Path = Field(..., description="Path to prequal test data Excel file")
    output_responses: Path = Field(..., description="Path for API responses")
    output_reports: Path = Field(..., description="Path for test reports")
    output_comparisons: Path = Field(..., description="Path for comparison results")
    output_processed: Path = Field(..., description="Path for processed JSON files")
    logs: Path = Field(..., description="Path for log files")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    model_config = ConfigDict(frozen=True)
    
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    max_bytes: int = Field(default=10485760, ge=1024, description="Max log file size in bytes")
    backup_count: int = Field(default=5, ge=1, le=20, description="Number of backup log files")
    
    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper


class ReportsConfig(BaseModel):
    """Report generation configuration."""
    
    model_config = ConfigDict(frozen=True)
    
    html_enabled: bool = Field(default=True, description="Enable HTML report generation")
    json_enabled: bool = Field(default=True, description="Enable JSON report generation")
    excel_enabled: bool = Field(default=True, description="Enable Excel report generation")
    include_response_preview: bool = Field(default=True, description="Include response preview in reports")
    preview_length: int = Field(default=200, ge=50, le=1000, description="Length of response preview")


class ApplicationConfig(BaseModel):
    """Complete application configuration."""
    
    model_config = ConfigDict(frozen=True)
    
    api: APIConfig
    test_execution: TestExecutionConfig
    test_data: TestDataConfig
    paths: PathsConfig
    logging: LoggingConfig
    reports: ReportsConfig


# ============================================================================
# Request/Response Models
# ============================================================================

class RequestResult(BaseModel):
    """Result of a single API request."""
    
    model_config = ConfigDict(
        use_enum_values=True,
        arbitrary_types_allowed=True
    )
    
    file_path: str = Field(..., description="Path to the request JSON file")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    response_text: str = Field(default="", description="Response body text")
    success: bool = Field(..., description="Whether the request was successful")
    error_message: Optional[str] = Field(None, description="Error message if request failed")
    response_time: float = Field(default=0.0, ge=0.0, description="Response time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    
    @property
    def file_name(self) -> str:
        """Get the base file name."""
        return Path(self.file_path).name
    
    @property
    def is_client_error(self) -> bool:
        """Check if status code indicates client error (4xx)."""
        return self.status_code is not None and 400 <= self.status_code < 500
    
    @property
    def is_server_error(self) -> bool:
        """Check if status code indicates server error (5xx)."""
        return self.status_code is not None and 500 <= self.status_code < 600


class BatchRequestResult(BaseModel):
    """Results of a batch of API requests."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    results: List[RequestResult] = Field(default_factory=list, description="Individual request results")
    total_requests: int = Field(..., ge=0, description="Total number of requests")
    successful_requests: int = Field(..., ge=0, description="Number of successful requests")
    failed_requests: int = Field(..., ge=0, description="Number of failed requests")
    avg_response_time: float = Field(..., ge=0.0, description="Average response time")
    total_execution_time: float = Field(..., ge=0.0, description="Total execution time")
    
    @model_validator(mode="after")
    def validate_counts(self) -> "BatchRequestResult":
        """Validate that counts match."""
        if self.successful_requests + self.failed_requests != self.total_requests:
            raise ValueError("Sum of successful and failed requests must equal total requests")
        return self


# ============================================================================
# Test Data Models
# ============================================================================

class AppIDRange(BaseModel):
    """APPID range configuration."""
    
    model_config = ConfigDict(frozen=True)
    
    start_value: Union[int, str] = Field(..., description="Starting APPID value")
    increment: int = Field(default=1, ge=1, description="Increment between IDs")
    count: Optional[int] = Field(None, ge=1, description="Number of IDs to generate")
    is_prequal: bool = Field(default=False, description="Whether this is prequal data")
    
    @field_validator("start_value")
    @classmethod
    def validate_start_value(cls, v: Union[int, str], info) -> Union[int, str]:
        """Validate start value based on type."""
        if isinstance(v, str):
            if not v.isdigit():
                raise ValueError("String start_value must contain only digits")
            if len(v) != 20:
                raise ValueError("Prequal APPID must be exactly 20 digits")
        elif isinstance(v, int):
            if v < 1:
                raise ValueError("Integer start_value must be positive")
        return v
    
    def generate_appids(self, count: Optional[int] = None) -> List[Union[int, str]]:
        """
        Generate a list of APPIDs.
        
        Args:
            count: Number of IDs to generate (uses self.count if not provided)
            
        Returns:
            List of generated APPIDs
        """
        num_ids = count or self.count
        if num_ids is None:
            raise ValueError("Count must be provided either in constructor or method call")
        
        appids = []
        if self.is_prequal:
            # Use Decimal for large number arithmetic
            current = Decimal(self.start_value)
            for _ in range(num_ids):
                appids.append(f"{current:020d}")
                current += self.increment
        else:
            current = int(self.start_value)
            for _ in range(num_ids):
                appids.append(current)
                current += self.increment
        
        return appids


class TestDataFile(BaseModel):
    """Information about a test data file."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    file_path: Path = Field(..., description="Path to the file")
    file_type: TestDataType = Field(..., description="Type of test data")
    appid_value: Union[int, str] = Field(..., description="APPID value for this file")
    processed: bool = Field(default=False, description="Whether file has been processed")
    
    @property
    def file_name(self) -> str:
        """Get the file name."""
        return self.file_path.name


# ============================================================================
# Comparison Models
# ============================================================================

class JSONDifference(BaseModel):
    """A single difference between two JSON structures."""
    
    model_config = ConfigDict(frozen=True)
    
    path: str = Field(..., description="JSON path where difference occurs")
    value_file1: str = Field(..., description="Value in first file")
    value_file2: str = Field(..., description="Value in second file")
    difference_type: str = Field(default="value_mismatch", description="Type of difference")


class FileComparisonResult(BaseModel):
    """Result of comparing two files."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    file_name: str = Field(..., description="Name of the compared file")
    has_differences: bool = Field(..., description="Whether differences were found")
    differences: List[JSONDifference] = Field(default_factory=list, description="List of differences")
    file1_status: str = Field(default="valid", description="Status of first file")
    file2_status: str = Field(default="valid", description="Status of second file")
    
    @property
    def difference_count(self) -> int:
        """Get the number of differences."""
        return len(self.differences)


class ComparisonSummary(BaseModel):
    """Summary of a comparison operation."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    folder1_name: str = Field(..., description="Name of first folder")
    folder2_name: str = Field(..., description="Name of second folder")
    total_common_files: int = Field(..., ge=0, description="Number of common files")
    files_with_differences: int = Field(..., ge=0, description="Files with differences")
    files_identical: int = Field(..., ge=0, description="Identical files")
    only_in_folder1: List[str] = Field(default_factory=list, description="Files only in folder 1")
    only_in_folder2: List[str] = Field(default_factory=list, description="Files only in folder 2")
    comparison_results: List[FileComparisonResult] = Field(
        default_factory=list,
        description="Detailed comparison results"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="Comparison timestamp")


# ============================================================================
# Report Models
# ============================================================================

class StatusCodeDistribution(BaseModel):
    """Distribution of HTTP status codes."""
    
    status_code: int = Field(..., description="HTTP status code")
    count: int = Field(..., ge=0, description="Number of occurrences")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of total")


class TestStatistics(BaseModel):
    """Test execution statistics."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    total_tests: int = Field(..., ge=0, description="Total number of tests")
    successful_tests: int = Field(..., ge=0, description="Number of successful tests")
    failed_tests: int = Field(..., ge=0, description="Number of failed tests")
    success_rate: float = Field(..., ge=0.0, le=100.0, description="Success rate percentage")
    avg_response_time: float = Field(..., ge=0.0, description="Average response time")
    max_response_time: float = Field(..., ge=0.0, description="Maximum response time")
    min_response_time: float = Field(..., ge=0.0, description="Minimum response time")
    total_execution_time: float = Field(..., ge=0.0, description="Total execution time")
    status_code_distribution: List[StatusCodeDistribution] = Field(
        default_factory=list,
        description="Distribution of status codes"
    )
    error_count: int = Field(default=0, ge=0, description="Number of errors detected")


class TestReport(BaseModel):
    """Complete test report."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    run_id: str = Field(..., description="Unique run identifier")
    execution_status: ExecutionStatus = Field(..., description="Overall execution status")
    statistics: TestStatistics = Field(..., description="Test statistics")
    results: List[RequestResult] = Field(default_factory=list, description="Individual test results")
    start_time: datetime = Field(..., description="Test start time")
    end_time: datetime = Field(..., description="Test end time")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Test configuration snapshot")
    
    @property
    def duration(self) -> float:
        """Get test duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()


# ============================================================================
# Merge Models
# ============================================================================

class MergeResult(BaseModel):
    """Result of merging CSV files."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    group_name: str = Field(..., description="Name of the merged group")
    file_count: int = Field(..., ge=0, description="Number of files merged")
    output_file: Optional[str] = Field(None, description="Path to output file")
    success: bool = Field(..., description="Whether merge was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class MergeSummary(BaseModel):
    """Summary of CSV merge operation."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    input_folder: str = Field(..., description="Input folder path")
    output_folder: str = Field(..., description="Output folder path")
    total_csv_files: int = Field(..., ge=0, description="Total CSV files processed")
    file_groups: int = Field(..., ge=0, description="Number of file groups")
    successful_merges: int = Field(..., ge=0, description="Successful merge operations")
    failed_merges: int = Field(..., ge=0, description="Failed merge operations")
    merge_results: List[MergeResult] = Field(default_factory=list, description="Individual merge results")
    timestamp: datetime = Field(default_factory=datetime.now, description="Merge timestamp")