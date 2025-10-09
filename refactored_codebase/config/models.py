"""
Configuration data models using Pydantic for validation and type safety.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum


class LogLevel(str, Enum):
    """Logging levels enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Environment types enumeration."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class APIConfig(BaseModel):
    """API configuration settings."""
    url: HttpUrl = Field(..., description="API endpoint URL")
    host: str = Field(..., description="API host header")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=False, description="SSL certificate verification")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, le=60.0, description="Delay between retries")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"


class TestConfig(BaseModel):
    """Test execution configuration."""
    parallel_count: int = Field(default=2, ge=1, le=50, description="Number of parallel threads")
    think_time: float = Field(default=3.0, ge=0.0, le=60.0, description="Think time between requests")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Batch size for processing")
    enable_comparison: bool = Field(default=True, description="Enable response comparison")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"


class AppIDConfig(BaseModel):
    """Application ID generation configuration."""
    start_range: int = Field(default=100000000, ge=1, description="Starting APPID range")
    end_range: int = Field(default=999999999, ge=1, description="Ending APPID range")
    prequal_start_range: int = Field(default=10000000000000000000, ge=1, description="Prequal APPID start range")
    prequal_end_range: int = Field(default=99999999999999999999, ge=1, description="Prequal APPID end range")
    increment: int = Field(default=1, ge=1, description="APPID increment value")
    
    @validator('end_range')
    def validate_ranges(cls, v, values):
        """Validate that end_range is greater than start_range."""
        if 'start_range' in values and v <= values['start_range']:
            raise ValueError('end_range must be greater than start_range')
        return v
    
    @validator('prequal_end_range')
    def validate_prequal_ranges(cls, v, values):
        """Validate that prequal_end_range is greater than prequal_start_range."""
        if 'prequal_start_range' in values and v <= values['prequal_start_range']:
            raise ValueError('prequal_end_range must be greater than prequal_start_range')
        return v
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"


class PathConfig(BaseModel):
    """Path configuration for directories and files."""
    # Data directories
    data_dir: Path = Field(default=Path("data"), description="Base data directory")
    requests_dir: Path = Field(default=Path("data/requests"), description="Request templates directory")
    testdata_dir: Path = Field(default=Path("data/testdata"), description="Test data directory")
    
    # Output directories  
    output_dir: Path = Field(default=Path("output"), description="Base output directory")
    responses_dir: Path = Field(default=Path("output/responses"), description="API responses directory")
    reports_dir: Path = Field(default=Path("output/reports"), description="Test reports directory")
    comparisons_dir: Path = Field(default=Path("output/comparisons"), description="Comparison results directory")
    merged_dir: Path = Field(default=Path("output/merged"), description="Merged results directory")
    logs_dir: Path = Field(default=Path("output/logs"), description="Log files directory")
    
    # Configuration files
    config_dir: Path = Field(default=Path("config"), description="Configuration directory")
    
    def ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        directories = [
            self.data_dir,
            self.requests_dir,
            self.testdata_dir,
            self.output_dir,
            self.responses_dir,
            self.reports_dir,
            self.comparisons_dir,
            self.merged_dir,
            self.logs_dir,
            self.config_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    date_format: str = Field(default="%Y-%m-%d %H:%M:%S", description="Date format")
    file_rotation: bool = Field(default=True, description="Enable log file rotation")
    max_file_size: str = Field(default="10MB", description="Maximum log file size")
    backup_count: int = Field(default=5, ge=1, le=50, description="Number of backup log files")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"


class DatabaseConfig(BaseModel):
    """Database configuration (for future use)."""
    enabled: bool = Field(default=False, description="Enable database storage")
    url: Optional[str] = Field(default=None, description="Database connection URL")
    pool_size: int = Field(default=5, ge=1, le=50, description="Connection pool size")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"