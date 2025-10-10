"""
Request models for API Test Framework using Pydantic v2.

Defines all request structures for both FullSet and Prequal APIs
with comprehensive validation and type safety.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, field_validator, model_validator

from api_test_framework.models.base import (
    AppIDModel,
    BaseModel,
    MetadataModel,
    ValidationMixin,
)


class RequestHeader(BaseModel, ValidationMixin):
    """Common header structure for API requests."""
    
    service_type: str = Field(
        ...,
        description="Type of service being requested",
        examples=["NewACQApp", "NewPreqApp"]
    )
    context_id: Optional[str] = Field(
        default="",
        description="Context identifier for the request"
    )
    submit_date: str = Field(
        ...,
        description="Date when request was submitted (DDMMYYYY format)"
    )
    submit_time: str = Field(
        ...,
        description="Time when request was submitted (H:MM:SS format)"
    )
    
    @field_validator('submit_date')
    @classmethod
    def validate_submit_date(cls, v: str) -> str:
        """Validate submit date format."""
        return cls.validate_date_format(v, "%d%m%Y")
    
    @field_validator('submit_time')
    @classmethod
    def validate_submit_time(cls, v: str) -> str:
        """Validate submit time format."""
        try:
            # Parse time in H:MM:SS or HH:MM:SS format
            time_parts = v.split(':')
            if len(time_parts) != 3:
                raise ValueError("Time must be in H:MM:SS format")
            
            hours, minutes, seconds = map(int, time_parts)
            if not (0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
                raise ValueError("Invalid time values")
            
            return v
        except (ValueError, TypeError):
            raise ValueError("Time must be in H:MM:SS format")


class ProductAttributes(BaseModel):
    """Product attributes for application info."""
    
    store_number: str = Field(
        default="",
        description="Store number identifier"
    )
    agent_id: str = Field(
        default="",
        description="Agent identifier"
    )


class BusinessUBO(BaseModel):
    """Business Ultimate Beneficial Owner information."""
    
    date_of_birth: str = Field(
        default="",
        description="Date of birth (DDMMYYYY format)"
    )
    citizenship: str = Field(default="", description="Citizenship")
    controller_identifier: str = Field(default="", description="Controller identifier")
    country_residence: str = Field(default="", description="Country of residence")
    first_name: str = Field(default="", description="First name")
    identification_number: str = Field(default="", description="Identification number")
    issuing_country: str = Field(default="", description="Issuing country")
    last_name: str = Field(default="", description="Last name")
    middle_name: str = Field(default="", description="Middle name")
    other_identification: str = Field(default="", description="Other identification")
    percent_ownership: str = Field(default="", description="Percentage of ownership")
    physical_address: str = Field(default="", description="Physical address")
    physical_address2: str = Field(default="", description="Physical address line 2")
    physical_city: str = Field(default="", description="Physical city")
    physical_state: str = Field(default="", description="Physical state")
    physical_zip: str = Field(default="", description="Physical ZIP code")
    ssn: str = Field(default="", description="Social Security Number")
    suffix: str = Field(default="", description="Name suffix")
    title_in_business: str = Field(default="", description="Title in business")
    citizen: str = Field(default="", description="Citizen status")
    unique_identifier: str = Field(default="", description="Unique identifier")


class BusinessInfo(BaseModel):
    """Business information for applications."""
    
    # UBO information
    busubo: List[BusinessUBO] = Field(
        default_factory=list,
        description="Business Ultimate Beneficial Owners"
    )
    
    # Business details
    bus_address: str = Field(default="", description="Business address")
    bus_address2: str = Field(default="", description="Business address line 2")
    bus_beneficial_owners: str = Field(default="", description="Beneficial owners")
    bus_city: str = Field(default="", description="Business city")
    bus_state: str = Field(default="", description="Business state")
    bus_zip: str = Field(default="", description="Business ZIP code")
    bus_phone: str = Field(default="", description="Business phone")
    
    # Controller information
    bus_controller_citizenship: str = Field(default="", description="Controller citizenship")
    bus_controller_country_residence: str = Field(default="", description="Controller country of residence")
    bus_controller_date_of_birth: str = Field(default="", description="Controller date of birth")
    bus_controller_first_name: str = Field(default="", description="Controller first name")
    bus_controller_last_name: str = Field(default="", description="Controller last name")
    bus_controller_middle_name: str = Field(default="", description="Controller middle name")
    bus_controller_ssn: str = Field(default="", description="Controller SSN")
    bus_controller_unique_identifier: str = Field(default="", description="Controller unique identifier")
    
    # Business characteristics
    bus_type: str = Field(default="", description="Business type")
    bus_nature_of_business: str = Field(default="", description="Nature of business")
    bus_sub_nature_of_business: str = Field(default="", description="Sub nature of business")
    legal_bus_name: str = Field(default="", description="Legal business name")
    business_trading_name: str = Field(default="", description="Business trading name")
    emboss_bus_name: str = Field(default="", description="Emboss business name")
    tsys_bus_name: str = Field(default="", description="TSYS business name")
    
    # Financial information
    gross_sales: str = Field(default="", description="Gross sales")
    number_employees: str = Field(default="", description="Number of employees")
    yrs_business: str = Field(default="", description="Years in business")
    bus_last_opened: str = Field(default="", description="When business last opened")
    
    # Additional fields
    greater_than_25: str = Field(default="Y", description="Greater than 25% ownership")
    tin: str = Field(default="", description="Tax Identification Number")
    liability: str = Field(default="", description="Liability information")


class PersonalInfo(BaseModel, ValidationMixin):
    """Personal information for applicants."""
    
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    middle_name: str = Field(default="", description="Middle name")
    prefix: str = Field(default="", description="Name prefix")
    suffix: str = Field(default="", description="Name suffix")
    
    # Address information
    addr1: str = Field(..., description="Primary address line 1")
    addr2: str = Field(default="", description="Primary address line 2")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    postal_code: str = Field(..., description="Postal code")
    
    # Physical address (if different)
    phys_addr1: str = Field(default="", description="Physical address line 1")
    phys_addr2: str = Field(default="", description="Physical address line 2")
    phys_city: str = Field(default="", description="Physical city")
    phys_state: str = Field(default="", description="Physical state")
    phys_postal_code: str = Field(default="", description="Physical postal code")
    
    # Customer controls
    cust_controls: Dict[str, str] = Field(
        default_factory=dict,
        description="Customer control settings"
    )
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_required_names(cls, v: str) -> str:
        """Validate required name fields."""
        return cls.validate_non_empty_string(v, "Name")
    
    @field_validator('postal_code')
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        """Validate postal code format."""
        # Remove spaces and validate length
        clean_code = v.replace(' ', '')
        if len(clean_code) < 5:
            raise ValueError("Postal code must be at least 5 characters")
        return clean_code


class EmploymentInfo(BaseModel, ValidationMixin):
    """Employment information for applicants."""
    
    net_yearly_house_inc: str = Field(
        default="",
        description="Net yearly household income"
    )
    source_of_income: str = Field(
        default="",
        description="Source of income"
    )
    yearly_house_inc: str = Field(
        default="",
        description="Yearly household income"
    )
    
    @field_validator('net_yearly_house_inc', 'yearly_house_inc')
    @classmethod
    def validate_income(cls, v: str) -> str:
        """Validate income values."""
        if v and not v.isdigit():
            raise ValueError("Income must be numeric")
        return v


class ApplicantInfo(BaseModel, ValidationMixin):
    """Complete applicant information."""
    
    # Basic information
    country: str = Field(default="US", description="Country")
    home_phone: str = Field(default="", description="Home phone number")
    work_phone: str = Field(default="", description="Work phone number")
    email: str = Field(..., description="Email address")
    date_of_birth: str = Field(..., description="Date of birth (DDMMYYYY)")
    tax_id: str = Field(..., description="Tax ID/SSN")
    
    # Financial information
    monthly_rent_mortgage: str = Field(default="", description="Monthly rent/mortgage")
    res_len: str = Field(default="", description="Residence length")
    resid_status: str = Field(default="", description="Residence status")
    req_cr_line_amt: str = Field(default="", description="Requested credit line amount")
    
    # Additional fields
    appl_user_agent: str = Field(default="", description="Application user agent")
    non_tax_source: str = Field(default="", description="Non-tax source")
    
    # Nested information
    personal_info: PersonalInfo = Field(..., description="Personal information")
    employment: EmploymentInfo = Field(
        default_factory=EmploymentInfo,
        description="Employment information"
    )
    partner_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Partner-specific data"
    )
    crahp: Dict[str, Any] = Field(
        default_factory=dict,
        description="Credit report and history data"
    )
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        return cls.validate_email_format(v)
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v: str) -> str:
        """Validate date of birth format."""
        return cls.validate_date_format(v, "%d%m%Y")
    
    @field_validator('home_phone', 'work_phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        if v:
            return cls.validate_phone_number(v)
        return v


class ApplicationInfo(BaseModel):
    """Application information container."""
    
    product_attr: ProductAttributes = Field(
        default_factory=ProductAttributes,
        description="Product attributes"
    )
    business: BusinessInfo = Field(
        default_factory=BusinessInfo,
        description="Business information"
    )
    applicant: Optional[ApplicantInfo] = Field(
        default=None,
        description="Applicant information (for prequal requests)"
    )


class DecisionRequest(BaseModel, AppIDModel):
    """Decision request information."""
    
    # Core fields
    second_look_offer_flag: str = Field(default="F", description="Second look offer flag")
    consent_flag: str = Field(default="AA", description="Consent flag")
    prq_id: str = Field(default="", description="Prequal ID")
    party_id: str = Field(default="", description="Party ID")
    channel_code: str = Field(default="", description="Channel code")
    
    # Dates
    instance_expiration_date: str = Field(default="", description="Instance expiration date")
    application_received_date: str = Field(default="", description="Application received date")
    application_submitted_date: str = Field(default="", description="Application submitted date")
    
    # API and offer information
    api_version: str = Field(default="", description="API version")
    offer_instance_type_cd: str = Field(default="", description="Offer instance type code")
    offer_instance_id: str = Field(default="", description="Offer instance ID")
    credit_strategy_channel_cd: str = Field(default="", description="Credit strategy channel code")
    
    # Application information
    application_info: ApplicationInfo = Field(
        default_factory=ApplicationInfo,
        description="Application information"
    )
    
    # Additional fields for prequal
    request_type: Optional[str] = Field(default=None, description="Request type")
    offer_instance_type: Optional[str] = Field(default=None, description="Offer instance type")
    offer_instance_uuid: Optional[str] = Field(default=None, description="Offer instance UUID")
    planned_purchase_amount: Optional[str] = Field(default=None, description="Planned purchase amount")
    application_type: Optional[str] = Field(default=None, description="Application type")
    
    # Nested objects for prequal
    header: Optional[Dict[str, Any]] = Field(default=None, description="Header information")
    partner: Optional[Dict[str, Any]] = Field(default=None, description="Partner information")
    audit: Optional[Dict[str, Any]] = Field(default=None, description="Audit information")
    referrer: Optional[Dict[str, Any]] = Field(default=None, description="Referrer information")
    misc: Optional[Dict[str, Any]] = Field(default=None, description="Miscellaneous information")
    ad_source: Optional[Dict[str, Any]] = Field(default=None, description="Ad source information")


class APIRequest(BaseModel, MetadataModel):
    """Base API request structure."""
    
    request_id: str = Field(
        default_factory=lambda: f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        description="Unique request identifier"
    )
    request_type: str = Field(..., description="Type of request (fullset/prequal)")
    
    @field_validator('request_type')
    @classmethod
    def validate_request_type(cls, v: str) -> str:
        """Validate request type."""
        valid_types = {'fullset', 'prequal'}
        if v.lower() not in valid_types:
            raise ValueError(f"request_type must be one of: {valid_types}")
        return v.lower()


class FullSetRequest(APIRequest):
    """Full set API request structure."""
    
    request_type: str = Field(default="fullset", description="Request type")
    
    application: Dict[str, Any] = Field(
        ...,
        description="Application data structure"
    )
    
    @model_validator(mode='after')
    def validate_application_structure(self) -> 'FullSetRequest':
        """Validate application structure has required fields."""
        required_fields = ['HEADER', 'DECISIONRQ']
        
        for field in required_fields:
            if field not in self.application:
                raise ValueError(f"Missing required field in application: {field}")
        
        return self
    
    def get_header(self) -> RequestHeader:
        """Get typed header from application data."""
        header_data = self.application.get('HEADER', {})
        return RequestHeader.model_validate(header_data)
    
    def get_decision_request(self) -> DecisionRequest:
        """Get typed decision request from application data."""
        decision_data = self.application.get('DECISIONRQ', {})
        return DecisionRequest.model_validate(decision_data)
    
    def set_app_id(self, app_id: Union[int, str]) -> None:
        """Set application ID in the request."""
        if 'DECISIONRQ' in self.application:
            self.application['DECISIONRQ']['APPID'] = str(app_id)


class PrequalRequest(APIRequest):
    """Prequal API request structure."""
    
    request_type: str = Field(default="prequal", description="Request type")
    
    prequal: Dict[str, Any] = Field(
        ...,
        description="Prequal data structure"
    )
    
    @model_validator(mode='after')
    def validate_prequal_structure(self) -> 'PrequalRequest':
        """Validate prequal structure has required fields."""
        required_fields = ['HEADER', 'DECISIONRQ']
        
        for field in required_fields:
            if field not in self.prequal:
                raise ValueError(f"Missing required field in prequal: {field}")
        
        return self
    
    def get_header(self) -> RequestHeader:
        """Get typed header from prequal data."""
        header_data = self.prequal.get('HEADER', {})
        return RequestHeader.model_validate(header_data)
    
    def get_decision_request(self) -> DecisionRequest:
        """Get typed decision request from prequal data."""
        decision_data = self.prequal.get('DECISIONRQ', {})
        return DecisionRequest.model_validate(decision_data)
    
    def set_app_id(self, app_id: Union[int, str]) -> None:
        """Set application ID in the request."""
        if 'DECISIONRQ' in self.prequal:
            self.prequal['DECISIONRQ']['APPID'] = str(app_id)
    
    def get_applicant_info(self) -> Optional[ApplicantInfo]:
        """Get typed applicant information if present."""
        decision_rq = self.prequal.get('DECISIONRQ', {})
        applicant_data = decision_rq.get('APPLICANT')
        
        if applicant_data:
            return ApplicantInfo.model_validate(applicant_data)
        return None