"""
Test execution and reporting models for API Test Framework using Pydantic v2.

Defines models for test execution, results, metrics, comparisons,
and reporting with comprehensive validation and type safety.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, field_validator, model_validator

from api_test_framework.models.base import (
    BaseModel,
    IdentifiableModel,
    MetadataModel,
    TimestampedModel,
    ValidationMixin,
)
from api_test_framework.models.response_models import APIResponse


class TestStatus(str, Enum):
    """Test execution status enumeration."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ComparisonType(str, Enum):
    """Comparison type enumeration."""
    
    EXACT = "exact"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report format enumeration."""
    
    HTML = "html"
    JSON = "json"
    EXCEL = "excel"
    CSV = "csv"
    PDF = "pdf"


class TestConfiguration(BaseModel, ValidationMixin):
    """Configuration for test execution."""
    
    # Test identification
    test_name: str = Field(..., description="Name of the test")
    test_description: Optional[str] = Field(default=None, description="Test description")
    test_type: str = Field(..., description="Type of test (fullset/prequal/mixed)")
    
    # Execution parameters
    parallel_count: int = Field(default=2, ge=1, le=50, description="Number of parallel requests")
    think_time: float = Field(default=3.0, ge=0.0, le=60.0, description="Think time between requests")
    batch_size: int = Field(default=10, ge=1, le=100, description="Batch size for processing")
    max_requests: Optional[int] = Field(default=None, ge=1, description="Maximum number of requests")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    
    # Data configuration
    app_id_start: Optional[Union[int, str]] = Field(default=None, description="Starting application ID")
    app_id_increment: int = Field(default=1, ge=1, description="Application ID increment")
    use_timestamp_suffix: bool = Field(default=False, description="Add timestamp to IDs")
    
    # Validation settings
    validate_responses: bool = Field(default=True, description="Enable response validation")
    expected_status_codes: List[int] = Field(
        default_factory=lambda: [200, 201, 202],
        description="Expected HTTP status codes"
    )
    required_response_fields: List[str] = Field(
        default_factory=list,
        description="Required fields in response"
    )
    
    @field_validator('test_type')
    @classmethod
    def validate_test_type(cls, v: str) -> str:
        """Validate test type."""
        valid_types = {'fullset', 'prequal', 'mixed'}
        if v.lower() not in valid_types:
            raise ValueError(f"test_type must be one of: {valid_types}")
        return v.lower()
    
    @field_validator('expected_status_codes')
    @classmethod
    def validate_status_codes(cls, v: List[int]) -> List[int]:
        """Validate HTTP status codes."""
        for code in v:
            if not (100 <= code <= 599):
                raise ValueError(f"Invalid HTTP status code: {code}")
        return v


class TestMetrics(BaseModel):
    """Performance and execution metrics for tests."""
    
    # Timing metrics
    start_time: datetime = Field(..., description="Test start time")
    end_time: Optional[datetime] = Field(default=None, description="Test end time")
    total_duration_ms: Optional[float] = Field(default=None, description="Total test duration in milliseconds")
    
    # Request metrics
    total_requests: int = Field(default=0, description="Total number of requests")
    successful_requests: int = Field(default=0, description="Number of successful requests")
    failed_requests: int = Field(default=0, description="Number of failed requests")
    
    # Performance metrics
    average_response_time_ms: Optional[float] = Field(default=None, description="Average response time")
    min_response_time_ms: Optional[float] = Field(default=None, description="Minimum response time")
    max_response_time_ms: Optional[float] = Field(default=None, description="Maximum response time")
    requests_per_second: Optional[float] = Field(default=None, description="Requests per second")
    
    # Data transfer metrics
    total_bytes_sent: Optional[int] = Field(default=None, description="Total bytes sent")
    total_bytes_received: Optional[int] = Field(default=None, description="Total bytes received")
    
    # Error metrics
    error_rate: Optional[float] = Field(default=None, description="Error rate as percentage")
    timeout_count: int = Field(default=0, description="Number of timeout errors")
    connection_error_count: int = Field(default=0, description="Number of connection errors")
    
    @model_validator(mode='after')
    def calculate_derived_metrics(self) -> 'TestMetrics':
        """Calculate derived metrics from base metrics."""
        # Calculate total duration
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            self.total_duration_ms = duration.total_seconds() * 1000
        
        # Calculate error rate
        if self.total_requests > 0:
            self.error_rate = (self.failed_requests / self.total_requests) * 100
        
        # Calculate requests per second
        if self.total_duration_ms and self.total_duration_ms > 0:
            duration_seconds = self.total_duration_ms / 1000
            self.requests_per_second = self.total_requests / duration_seconds
        
        return self
    
    def update_response_time_stats(self, response_time_ms: float) -> None:
        """Update response time statistics with new measurement."""
        if self.min_response_time_ms is None or response_time_ms < self.min_response_time_ms:
            self.min_response_time_ms = response_time_ms
        
        if self.max_response_time_ms is None or response_time_ms > self.max_response_time_ms:
            self.max_response_time_ms = response_time_ms
        
        # Update average (simplified - in practice, you'd want running average)
        if self.average_response_time_ms is None:
            self.average_response_time_ms = response_time_ms
        else:
            # Simple average update - could be improved with proper running average
            total_time = self.average_response_time_ms * (self.total_requests - 1) + response_time_ms
            self.average_response_time_ms = total_time / self.total_requests


class TestResult(IdentifiableModel):
    """Individual test result."""
    
    # Test identification
    test_name: str = Field(..., description="Name of the test")
    request_id: str = Field(..., description="Request identifier")
    app_id: Union[int, str] = Field(..., description="Application ID used")
    
    # Execution details
    status: TestStatus = Field(..., description="Test execution status")
    start_time: datetime = Field(..., description="Test start time")
    end_time: Optional[datetime] = Field(default=None, description="Test end time")
    
    # Request/Response data
    request_data: Dict[str, Any] = Field(default_factory=dict, description="Request data sent")
    response: Optional[APIResponse] = Field(default=None, description="API response received")
    
    # Validation results
    validation_passed: bool = Field(default=True, description="Whether validation passed")
    validation_errors: List[str] = Field(default_factory=list, description="Validation error messages")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    # Error information
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed error information")
    
    # Performance metrics
    response_time_ms: Optional[float] = Field(default=None, description="Response time in milliseconds")
    request_size_bytes: Optional[int] = Field(default=None, description="Request size in bytes")
    response_size_bytes: Optional[int] = Field(default=None, description="Response size in bytes")
    
    @model_validator(mode='after')
    def validate_test_result_consistency(self) -> 'TestResult':
        """Validate test result data consistency."""
        # If status is failed, should have error information
        if self.status == TestStatus.FAILED and not self.error_message:
            self.error_message = "Test failed but no error message provided"
        
        # If validation failed, status should reflect that
        if not self.validation_passed and self.status == TestStatus.COMPLETED:
            self.status = TestStatus.FAILED
            if not self.error_message:
                self.error_message = "Validation failed"
        
        # Extract response time from response if available
        if self.response and self.response.metrics and not self.response_time_ms:
            self.response_time_ms = self.response.metrics.response_time_ms
        
        return self
    
    def is_successful(self) -> bool:
        """Check if test result is successful."""
        return (
            self.status == TestStatus.COMPLETED and
            self.validation_passed and
            self.response is not None and
            self.response.success
        )
    
    def get_duration_ms(self) -> Optional[float]:
        """Get test duration in milliseconds."""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return duration.total_seconds() * 1000
        return None


class TestExecution(IdentifiableModel):
    """Test execution session."""
    
    # Execution identification
    run_id: str = Field(
        default_factory=lambda: f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}",
        description="Unique run identifier"
    )
    execution_name: str = Field(..., description="Name of the test execution")
    
    # Configuration
    configuration: TestConfiguration = Field(..., description="Test configuration")
    
    # Execution state
    status: TestStatus = Field(default=TestStatus.PENDING, description="Execution status")
    start_time: Optional[datetime] = Field(default=None, description="Execution start time")
    end_time: Optional[datetime] = Field(default=None, description="Execution end time")
    
    # Results
    test_results: List[TestResult] = Field(default_factory=list, description="Individual test results")
    metrics: Optional[TestMetrics] = Field(default=None, description="Execution metrics")
    
    # Output paths
    output_directory: Optional[Path] = Field(default=None, description="Output directory path")
    log_file: Optional[Path] = Field(default=None, description="Log file path")
    
    # Error information
    execution_errors: List[str] = Field(default_factory=list, description="Execution-level errors")
    
    def start_execution(self) -> None:
        """Mark execution as started."""
        self.status = TestStatus.RUNNING
        self.start_time = datetime.now(timezone.utc)
        
        # Initialize metrics
        self.metrics = TestMetrics(start_time=self.start_time)
    
    def complete_execution(self) -> None:
        """Mark execution as completed and calculate final metrics."""
        self.end_time = datetime.now(timezone.utc)
        self.status = TestStatus.COMPLETED
        
        if self.metrics:
            self.metrics.end_time = self.end_time
            self.metrics.total_requests = len(self.test_results)
            self.metrics.successful_requests = sum(1 for r in self.test_results if r.is_successful())
            self.metrics.failed_requests = self.metrics.total_requests - self.metrics.successful_requests
            
            # Calculate response time statistics
            response_times = [r.response_time_ms for r in self.test_results if r.response_time_ms]
            if response_times:
                self.metrics.average_response_time_ms = sum(response_times) / len(response_times)
                self.metrics.min_response_time_ms = min(response_times)
                self.metrics.max_response_time_ms = max(response_times)
    
    def fail_execution(self, error_message: str) -> None:
        """Mark execution as failed."""
        self.status = TestStatus.FAILED
        self.end_time = datetime.now(timezone.utc)
        self.execution_errors.append(error_message)
    
    def add_test_result(self, test_result: TestResult) -> None:
        """Add a test result to the execution."""
        self.test_results.append(test_result)
        
        # Update metrics if available
        if self.metrics and test_result.response_time_ms:
            self.metrics.update_response_time_stats(test_result.response_time_ms)
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if not self.test_results:
            return 0.0
        
        successful = sum(1 for r in self.test_results if r.is_successful())
        return (successful / len(self.test_results)) * 100.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return {
            "run_id": self.run_id,
            "execution_name": self.execution_name,
            "status": self.status.value,
            "total_tests": len(self.test_results),
            "successful_tests": sum(1 for r in self.test_results if r.is_successful()),
            "success_rate": self.get_success_rate(),
            "duration_ms": self.metrics.total_duration_ms if self.metrics else None,
            "average_response_time_ms": self.metrics.average_response_time_ms if self.metrics else None,
        }


class TestSuite(IdentifiableModel):
    """Collection of test executions."""
    
    # Suite identification
    suite_name: str = Field(..., description="Name of the test suite")
    suite_description: Optional[str] = Field(default=None, description="Suite description")
    
    # Executions
    executions: List[TestExecution] = Field(default_factory=list, description="Test executions")
    
    # Suite configuration
    suite_configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="Suite-level configuration"
    )
    
    def add_execution(self, execution: TestExecution) -> None:
        """Add a test execution to the suite."""
        self.executions.append(execution)
    
    def get_total_tests(self) -> int:
        """Get total number of tests across all executions."""
        return sum(len(exec.test_results) for exec in self.executions)
    
    def get_overall_success_rate(self) -> float:
        """Get overall success rate across all executions."""
        total_tests = 0
        successful_tests = 0
        
        for execution in self.executions:
            total_tests += len(execution.test_results)
            successful_tests += sum(1 for r in execution.test_results if r.is_successful())
        
        if total_tests == 0:
            return 0.0
        
        return (successful_tests / total_tests) * 100.0


class ComparisonDifference(BaseModel):
    """Represents a difference found during comparison."""
    
    path: str = Field(..., description="JSON path where difference was found")
    difference_type: str = Field(..., description="Type of difference")
    old_value: Any = Field(default=None, description="Value in first object")
    new_value: Any = Field(default=None, description="Value in second object")
    severity: str = Field(default="INFO", description="Severity of the difference")
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity level."""
        valid_severities = {'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_severities:
            raise ValueError(f"severity must be one of: {valid_severities}")
        return v.upper()


class ComparisonResult(IdentifiableModel):
    """Result of comparing two API responses or data structures."""
    
    # Comparison identification
    comparison_name: str = Field(..., description="Name of the comparison")
    comparison_type: ComparisonType = Field(..., description="Type of comparison performed")
    
    # Source information
    source_file: Optional[str] = Field(default=None, description="Source file path")
    target_file: Optional[str] = Field(default=None, description="Target file path")
    source_id: Optional[str] = Field(default=None, description="Source identifier")
    target_id: Optional[str] = Field(default=None, description="Target identifier")
    
    # Comparison results
    are_equal: bool = Field(..., description="Whether objects are considered equal")
    differences: List[ComparisonDifference] = Field(
        default_factory=list,
        description="List of differences found"
    )
    
    # Statistics
    total_fields_compared: int = Field(default=0, description="Total number of fields compared")
    matching_fields: int = Field(default=0, description="Number of matching fields")
    different_fields: int = Field(default=0, description="Number of different fields")
    
    # Performance
    comparison_duration_ms: Optional[float] = Field(
        default=None,
        description="Time taken to perform comparison"
    )
    
    @model_validator(mode='after')
    def calculate_comparison_stats(self) -> 'ComparisonResult':
        """Calculate comparison statistics."""
        self.different_fields = len(self.differences)
        
        if self.total_fields_compared > 0:
            self.matching_fields = self.total_fields_compared - self.different_fields
        
        return self
    
    def add_difference(
        self,
        path: str,
        difference_type: str,
        old_value: Any = None,
        new_value: Any = None,
        severity: str = "INFO"
    ) -> None:
        """Add a difference to the comparison result."""
        difference = ComparisonDifference(
            path=path,
            difference_type=difference_type,
            old_value=old_value,
            new_value=new_value,
            severity=severity
        )
        self.differences.append(difference)
        self.are_equal = False
    
    def get_differences_by_severity(self, severity: str) -> List[ComparisonDifference]:
        """Get differences filtered by severity."""
        return [d for d in self.differences if d.severity == severity.upper()]
    
    def get_similarity_percentage(self) -> float:
        """Get similarity percentage."""
        if self.total_fields_compared == 0:
            return 100.0
        
        return (self.matching_fields / self.total_fields_compared) * 100.0


class ReportData(TimestampedModel, MetadataModel):
    """Data structure for generating reports."""
    
    # Report identification
    report_id: str = Field(
        default_factory=lambda: f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        description="Unique report identifier"
    )
    report_title: str = Field(..., description="Report title")
    report_type: str = Field(..., description="Type of report")
    
    # Data sources
    test_executions: List[TestExecution] = Field(
        default_factory=list,
        description="Test executions included in report"
    )
    comparison_results: List[ComparisonResult] = Field(
        default_factory=list,
        description="Comparison results included in report"
    )
    
    # Report configuration
    include_charts: bool = Field(default=True, description="Include charts in report")
    include_raw_data: bool = Field(default=False, description="Include raw data in report")
    chart_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chart configuration settings"
    )
    
    # Summary statistics
    summary_stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary statistics for the report"
    )
    
    @model_validator(mode='after')
    def calculate_summary_stats(self) -> 'ReportData':
        """Calculate summary statistics for the report."""
        stats = {}
        
        # Test execution statistics
        if self.test_executions:
            total_tests = sum(len(exec.test_results) for exec in self.test_executions)
            successful_tests = sum(
                sum(1 for r in exec.test_results if r.is_successful())
                for exec in self.test_executions
            )
            
            stats.update({
                "total_executions": len(self.test_executions),
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "overall_success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            })
            
            # Response time statistics
            all_response_times = []
            for exec in self.test_executions:
                for result in exec.test_results:
                    if result.response_time_ms:
                        all_response_times.append(result.response_time_ms)
            
            if all_response_times:
                stats.update({
                    "average_response_time_ms": sum(all_response_times) / len(all_response_times),
                    "min_response_time_ms": min(all_response_times),
                    "max_response_time_ms": max(all_response_times),
                })
        
        # Comparison statistics
        if self.comparison_results:
            total_comparisons = len(self.comparison_results)
            equal_comparisons = sum(1 for c in self.comparison_results if c.are_equal)
            
            stats.update({
                "total_comparisons": total_comparisons,
                "equal_comparisons": equal_comparisons,
                "different_comparisons": total_comparisons - equal_comparisons,
                "comparison_match_rate": (equal_comparisons / total_comparisons * 100) if total_comparisons > 0 else 0,
            })
        
        self.summary_stats = stats
        return self
    
    def add_test_execution(self, execution: TestExecution) -> None:
        """Add a test execution to the report."""
        self.test_executions.append(execution)
    
    def add_comparison_result(self, comparison: ComparisonResult) -> None:
        """Add a comparison result to the report."""
        self.comparison_results.append(comparison)