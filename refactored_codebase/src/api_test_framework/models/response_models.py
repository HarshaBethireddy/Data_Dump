"""
Response models for API Test Framework using Pydantic v2.

Defines all response structures for API calls with comprehensive
validation, error handling, and type safety.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, field_validator, model_validator

from api_test_framework.models.base import (
    BaseModel,
    IdentifiableModel,
    MetadataModel,
    TimestampedModel,
    ValidationMixin,
)


class ResponseHeader(BaseModel, ValidationMixin):
    """Response header information."""
    
    service_type: str = Field(..., description="Service type from response")
    context_id: Optional[str] = Field(default=None, description="Context identifier")
    response_date: Optional[str] = Field(default=None, description="Response date")
    response_time: Optional[str] = Field(default=None, description="Response time")
    transaction_id: Optional[str] = Field(default=None, description="Transaction identifier")
    
    @field_validator('response_date')
    @classmethod
    def validate_response_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate response date format if provided."""
        if v:
            return cls.validate_date_format(v, "%d%m%Y")
        return v


class DecisionResponse(BaseModel):
    """Decision response from API."""
    
    decision: Optional[str] = Field(default=None, description="Decision result")
    decision_code: Optional[str] = Field(default=None, description="Decision code")
    decision_reason: Optional[str] = Field(default=None, description="Decision reason")
    credit_limit: Optional[Union[int, str]] = Field(default=None, description="Approved credit limit")
    apr: Optional[Union[float, str]] = Field(default=None, description="Annual Percentage Rate")
    
    # Offer information
    offer_id: Optional[str] = Field(default=None, description="Offer identifier")
    offer_type: Optional[str] = Field(default=None, description="Offer type")
    offer_expiry: Optional[str] = Field(default=None, description="Offer expiry date")
    
    # Additional decision data
    risk_score: Optional[Union[int, float]] = Field(default=None, description="Risk score")
    bureau_score: Optional[Union[int, float]] = Field(default=None, description="Bureau score")
    
    # Custom fields for different response types
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom response fields"
    )
    
    @field_validator('credit_limit')
    @classmethod
    def validate_credit_limit(cls, v: Optional[Union[int, str]]) -> Optional[Union[int, str]]:
        """Validate credit limit format."""
        if v is not None:
            if isinstance(v, str) and v.strip():
                if not v.isdigit():
                    raise ValueError("Credit limit must be numeric")
            elif isinstance(v, (int, float)) and v < 0:
                raise ValueError("Credit limit cannot be negative")
        return v
    
    @field_validator('apr')
    @classmethod
    def validate_apr(cls, v: Optional[Union[float, str]]) -> Optional[Union[float, str]]:
        """Validate APR format."""
        if v is not None:
            try:
                apr_float = float(v)
                if apr_float < 0 or apr_float > 100:
                    raise ValueError("APR must be between 0 and 100")
            except (ValueError, TypeError):
                raise ValueError("APR must be a valid number")
        return v


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    error_field: Optional[str] = Field(default=None, description="Field that caused the error")
    error_severity: str = Field(default="ERROR", description="Error severity level")
    
    @field_validator('error_severity')
    @classmethod
    def validate_error_severity(cls, v: str) -> str:
        """Validate error severity level."""
        valid_severities = {'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_severities:
            raise ValueError(f"error_severity must be one of: {valid_severities}")
        return v.upper()


class ErrorResponse(BaseModel):
    """Error response structure."""
    
    error: bool = Field(default=True, description="Indicates this is an error response")
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Main error message")
    error_details: List[ErrorDetail] = Field(
        default_factory=list,
        description="Detailed error information"
    )
    
    # HTTP-specific error information
    status_code: Optional[int] = Field(default=None, description="HTTP status code")
    request_id: Optional[str] = Field(default=None, description="Request identifier")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Error timestamp"
    )
    
    @field_validator('status_code')
    @classmethod
    def validate_status_code(cls, v: Optional[int]) -> Optional[int]:
        """Validate HTTP status code."""
        if v is not None and (v < 100 or v > 599):
            raise ValueError("status_code must be a valid HTTP status code (100-599)")
        return v
    
    def add_error_detail(
        self,
        error_code: str,
        error_message: str,
        error_field: Optional[str] = None,
        error_severity: str = "ERROR"
    ) -> None:
        """Add an error detail to the response."""
        detail = ErrorDetail(
            error_code=error_code,
            error_message=error_message,
            error_field=error_field,
            error_severity=error_severity
        )
        self.error_details.append(detail)


class ValidationResult(BaseModel):
    """Result of data validation."""
    
    is_valid: bool = Field(..., description="Whether validation passed")
    validation_errors: List[str] = Field(
        default_factory=list,
        description="List of validation error messages"
    )
    validation_warnings: List[str] = Field(
        default_factory=list,
        description="List of validation warnings"
    )
    validated_fields: List[str] = Field(
        default_factory=list,
        description="List of successfully validated fields"
    )
    
    def add_error(self, error_message: str) -> None:
        """Add a validation error."""
        self.validation_errors.append(error_message)
        self.is_valid = False
    
    def add_warning(self, warning_message: str) -> None:
        """Add a validation warning."""
        self.validation_warnings.append(warning_message)
    
    def add_validated_field(self, field_name: str) -> None:
        """Add a successfully validated field."""
        if field_name not in self.validated_fields:
            self.validated_fields.append(field_name)


class ResponseMetrics(BaseModel):
    """Performance metrics for API responses."""
    
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    request_size_bytes: Optional[int] = Field(default=None, description="Request size in bytes")
    response_size_bytes: Optional[int] = Field(default=None, description="Response size in bytes")
    
    # Network metrics
    dns_lookup_time_ms: Optional[float] = Field(default=None, description="DNS lookup time")
    tcp_connect_time_ms: Optional[float] = Field(default=None, description="TCP connect time")
    ssl_handshake_time_ms: Optional[float] = Field(default=None, description="SSL handshake time")
    
    # Processing metrics
    server_processing_time_ms: Optional[float] = Field(default=None, description="Server processing time")
    
    @field_validator('response_time_ms')
    @classmethod
    def validate_response_time(cls, v: float) -> float:
        """Validate response time is positive."""
        if v < 0:
            raise ValueError("response_time_ms cannot be negative")
        return v


class APIResponse(TimestampedModel, MetadataModel):
    """Base API response structure."""
    
    # Request correlation
    request_id: str = Field(..., description="Corresponding request identifier")
    correlation_id: Optional[str] = Field(default=None, description="Request correlation ID")
    
    # Response status
    success: bool = Field(..., description="Whether the request was successful")
    status_code: int = Field(..., description="HTTP status code")
    status_message: Optional[str] = Field(default=None, description="HTTP status message")
    
    # Response data
    response_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw response data"
    )
    
    # Headers and metadata
    response_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP response headers"
    )
    
    # Performance metrics
    metrics: Optional[ResponseMetrics] = Field(
        default=None,
        description="Response performance metrics"
    )
    
    # Error information (if applicable)
    error_response: Optional[ErrorResponse] = Field(
        default=None,
        description="Error details if request failed"
    )
    
    # Validation results
    validation_result: Optional[ValidationResult] = Field(
        default=None,
        description="Response validation results"
    )
    
    @model_validator(mode='after')
    def validate_response_consistency(self) -> 'APIResponse':
        """Validate response data consistency."""
        # If not successful, should have error information
        if not self.success and self.error_response is None:
            self.error_response = ErrorResponse(
                error_type="UNKNOWN_ERROR",
                error_message="Request failed but no error details provided",
                status_code=self.status_code
            )
        
        # If successful, should not have error response
        if self.success and self.error_response is not None:
            self.success = False
        
        return self
    
    def get_header(self) -> Optional[ResponseHeader]:
        """Get typed response header if present."""
        if 'HEADER' in self.response_data:
            try:
                return ResponseHeader.model_validate(self.response_data['HEADER'])
            except Exception:
                return None
        return None
    
    def get_decision_response(self) -> Optional[DecisionResponse]:
        """Get typed decision response if present."""
        # Try different possible locations for decision data
        decision_locations = ['DECISIONRS', 'DECISION', 'RESPONSE']
        
        for location in decision_locations:
            if location in self.response_data:
                try:
                    return DecisionResponse.model_validate(self.response_data[location])
                except Exception:
                    continue
        
        # Try to extract decision data from root level
        try:
            return DecisionResponse.model_validate(self.response_data)
        except Exception:
            return None
    
    def is_successful_decision(self) -> bool:
        """Check if response contains a successful decision."""
        if not self.success:
            return False
        
        decision = self.get_decision_response()
        if decision and decision.decision:
            # Common successful decision values
            successful_decisions = {'APPROVED', 'ACCEPT', 'YES', 'PASS'}
            return decision.decision.upper() in successful_decisions
        
        return False
    
    def get_response_time_seconds(self) -> Optional[float]:
        """Get response time in seconds."""
        if self.metrics and self.metrics.response_time_ms:
            return self.metrics.response_time_ms / 1000.0
        return None
    
    def add_validation_error(self, error_message: str) -> None:
        """Add a validation error to the response."""
        if self.validation_result is None:
            self.validation_result = ValidationResult(is_valid=True)
        
        self.validation_result.add_error(error_message)
    
    def add_validation_warning(self, warning_message: str) -> None:
        """Add a validation warning to the response."""
        if self.validation_result is None:
            self.validation_result = ValidationResult(is_valid=True)
        
        self.validation_result.add_warning(warning_message)


class FullSetResponse(APIResponse):
    """Full set API response structure."""
    
    def get_application_response(self) -> Dict[str, Any]:
        """Get application response data."""
        return self.response_data.get('APPLICATION', {})


class PrequalResponse(APIResponse):
    """Prequal API response structure."""
    
    def get_prequal_response(self) -> Dict[str, Any]:
        """Get prequal response data."""
        return self.response_data.get('PREQUAL', {})
    
    def get_bureau_response(self) -> Optional[Dict[str, Any]]:
        """Get bureau response data if present."""
        prequal_data = self.get_prequal_response()
        return prequal_data.get('BUREAU', None)


class BatchResponse(BaseModel):
    """Response for batch operations."""
    
    batch_id: str = Field(..., description="Batch identifier")
    total_requests: int = Field(..., description="Total number of requests in batch")
    successful_requests: int = Field(default=0, description="Number of successful requests")
    failed_requests: int = Field(default=0, description="Number of failed requests")
    
    # Individual responses
    responses: List[APIResponse] = Field(
        default_factory=list,
        description="Individual API responses"
    )
    
    # Batch metrics
    total_processing_time_ms: float = Field(..., description="Total batch processing time")
    average_response_time_ms: Optional[float] = Field(default=None, description="Average response time")
    
    # Error summary
    error_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Summary of errors by type"
    )
    
    @model_validator(mode='after')
    def calculate_batch_metrics(self) -> 'BatchResponse':
        """Calculate batch-level metrics."""
        if self.responses:
            # Count successful and failed requests
            self.successful_requests = sum(1 for r in self.responses if r.success)
            self.failed_requests = len(self.responses) - self.successful_requests
            
            # Calculate average response time
            response_times = [
                r.metrics.response_time_ms for r in self.responses 
                if r.metrics and r.metrics.response_time_ms
            ]
            if response_times:
                self.average_response_time_ms = sum(response_times) / len(response_times)
            
            # Build error summary
            error_types = {}
            for response in self.responses:
                if not response.success and response.error_response:
                    error_type = response.error_response.error_type
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            self.error_summary = error_types
        
        return self
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    def add_response(self, response: APIResponse) -> None:
        """Add a response to the batch."""
        self.responses.append(response)
        self.total_requests = len(self.responses)