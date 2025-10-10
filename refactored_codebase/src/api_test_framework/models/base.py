"""
Base models and utilities for API Test Framework using Pydantic v2.

Provides common base classes, validators, and utilities that are
shared across all model types in the framework.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, field_validator, model_validator


class BaseModel(PydanticBaseModel):
    """
    Enhanced base model with common functionality for all framework models.
    
    Features:
    - Automatic field validation
    - JSON serialization with custom encoders
    - Model configuration for performance and validation
    - Common utility methods
    """
    
    model_config = ConfigDict(
        # Performance optimizations
        validate_assignment=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        
        # Serialization settings
        ser_json_timedelta='float',
        ser_json_bytes='base64',
        
        # Validation settings
        str_strip_whitespace=True,
        validate_default=True,
        
        # Extra fields handling
        extra='forbid',
        
        # JSON schema generation
        json_schema_extra={
            "examples": []
        }
    )
    
    def to_dict(self, exclude_none: bool = True, by_alias: bool = True) -> Dict[str, Any]:
        """Convert model to dictionary with customizable options."""
        return self.model_dump(
            exclude_none=exclude_none,
            by_alias=by_alias,
            mode='json'
        )
    
    def to_json(self, exclude_none: bool = True, by_alias: bool = True) -> str:
        """Convert model to JSON string."""
        return self.model_dump_json(
            exclude_none=exclude_none,
            by_alias=by_alias,
            indent=2
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model instance from dictionary."""
        return cls.model_validate(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BaseModel':
        """Create model instance from JSON string."""
        return cls.model_validate_json(json_str)
    
    def update_from_dict(self, data: Dict[str, Any]) -> 'BaseModel':
        """Update model with data from dictionary."""
        updated_data = self.to_dict()
        updated_data.update(data)
        return self.__class__.from_dict(updated_data)


class TimestampedModel(BaseModel):
    """
    Base model with automatic timestamp tracking.
    
    Automatically adds created_at and updated_at fields with
    proper timezone handling and validation.
    """
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the record was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the record was last updated"
    )
    
    @field_validator('created_at', 'updated_at')
    @classmethod
    def validate_timestamps(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure timestamps are timezone-aware."""
        if v is None:
            return v
        
        if v.tzinfo is None:
            # Assume UTC if no timezone info
            return v.replace(tzinfo=timezone.utc)
        
        return v
    
    @model_validator(mode='before')
    @classmethod
    def set_updated_at(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically set updated_at when model is modified."""
        if isinstance(values, dict):
            # Only set updated_at if this is an update (has created_at)
            if 'created_at' in values and 'updated_at' not in values:
                values['updated_at'] = datetime.now(timezone.utc)
        return values


class IdentifiableModel(TimestampedModel):
    """
    Base model with unique identifier and timestamp tracking.
    
    Provides automatic UUID generation and timestamp management
    for models that need unique identification.
    """
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the record"
    )
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that ID is a valid UUID format."""
        try:
            # Validate UUID format
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")


class AppIDModel(BaseModel):
    """
    Base model for handling Application IDs with proper validation.
    
    Supports both regular integer IDs and 20-digit prequal IDs
    with appropriate validation and formatting.
    """
    
    app_id: Union[int, str] = Field(
        ...,
        description="Application ID - integer for regular, 20-digit string for prequal"
    )
    app_id_type: str = Field(
        default="regular",
        description="Type of application ID: 'regular' or 'prequal'"
    )
    
    @field_validator('app_id_type')
    @classmethod
    def validate_app_id_type(cls, v: str) -> str:
        """Validate application ID type."""
        valid_types = {'regular', 'prequal'}
        if v not in valid_types:
            raise ValueError(f"app_id_type must be one of: {valid_types}")
        return v
    
    @model_validator(mode='after')
    def validate_app_id_format(self) -> 'AppIDModel':
        """Validate application ID format based on type."""
        if self.app_id_type == 'regular':
            if not isinstance(self.app_id, int) or self.app_id <= 0:
                raise ValueError("Regular app_id must be a positive integer")
        
        elif self.app_id_type == 'prequal':
            if isinstance(self.app_id, int):
                # Convert to 20-digit string
                self.app_id = f"{self.app_id:020d}"
            elif isinstance(self.app_id, str):
                if not self.app_id.isdigit() or len(self.app_id) != 20:
                    raise ValueError("Prequal app_id must be exactly 20 digits")
            else:
                raise ValueError("Prequal app_id must be string or integer")
        
        return self
    
    def get_formatted_app_id(self) -> str:
        """Get properly formatted application ID as string."""
        if self.app_id_type == 'prequal':
            return str(self.app_id)
        else:
            return str(self.app_id)


class ValidationMixin:
    """
    Mixin class providing common validation utilities.
    
    Can be used with any Pydantic model to add standard
    validation methods and utilities.
    """
    
    @classmethod
    def validate_non_empty_string(cls, v: str, field_name: str = "field") -> str:
        """Validate that string is not empty after stripping."""
        if not v or not v.strip():
            raise ValueError(f"{field_name} cannot be empty")
        return v.strip()
    
    @classmethod
    def validate_positive_number(cls, v: Union[int, float], field_name: str = "field") -> Union[int, float]:
        """Validate that number is positive."""
        if v <= 0:
            raise ValueError(f"{field_name} must be positive")
        return v
    
    @classmethod
    def validate_date_format(cls, v: str, date_format: str = "%d%m%Y") -> str:
        """Validate date string format."""
        try:
            datetime.strptime(v, date_format)
            return v
        except ValueError:
            raise ValueError(f"Date must be in format {date_format}")
    
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format."""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        
        if len(digits_only) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        
        return digits_only
    
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Basic email format validation."""
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError("Invalid email format")
        return v.lower().strip()


class MetadataModel(BaseModel):
    """
    Model for storing metadata information.
    
    Provides a flexible structure for storing additional
    metadata that doesn't fit into specific model fields.
    """
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata as key-value pairs"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering"
    )
    version: str = Field(
        default="1.0",
        description="Version of the data structure"
    )
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags."""
        return [tag.strip().lower() for tag in v if tag.strip()]
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        if not v or not v.strip():
            raise ValueError("Version cannot be empty")
        return v.strip()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata key-value pair."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key."""
        return self.metadata.get(key, default)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag if not already present."""
        normalized_tag = tag.strip().lower()
        if normalized_tag and normalized_tag not in self.tags:
            self.tags.append(normalized_tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if tag exists."""
        return tag.strip().lower() in self.tags