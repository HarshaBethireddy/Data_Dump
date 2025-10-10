"""
Enterprise-grade configuration management using Pydantic v2.

Features:
- JSON-based configuration with environment variable overrides
- Pydantic v2 validation and serialization
- Type-safe configuration access
- Nested configuration models
- Default values and validation rules
- Configuration hot-reloading support
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class APIEndpointConfig(BaseModel):
    """Configuration for API endpoints."""
    
    url: str = Field(..., description="Base API URL")
    host: str = Field(..., description="Host header value")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=False, description="Enable SSL certificate verification")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, le=60.0, description="Delay between retries in seconds")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.rstrip('/')


class TestExecutionConfig(BaseModel):
    """Configuration for test execution."""
    
    parallel_count: int = Field(default=2, ge=1, le=50, description="Number of parallel requests")
    think_time: float = Field(default=3.0, ge=0.0, le=60.0, description="Think time between requests in seconds")
    batch_size: int = Field(default=10, ge=1, le=100, description="Batch size for processing")
    enable_async: bool = Field(default=True, description="Enable async execution")
    connection_pool_size: int = Field(default=20, ge=1, le=100, description="HTTP connection pool size")


class AppIDConfig(BaseModel):
    """Configuration for Application ID generation."""
    
    regular_start: int = Field(default=1000000, ge=1, description="Starting value for regular app IDs")
    regular_increment: int = Field(default=1, ge=1, description="Increment value for regular app IDs")
    prequal_start: str = Field(default="10000000000000000000", description="Starting value for prequal app IDs (20 digits)")
    prequal_increment: int = Field(default=1, ge=1, description="Increment value for prequal app IDs")
    use_timestamp_suffix: bool = Field(default=False, description="Append timestamp to generated IDs")
    
    @field_validator('prequal_start')
    @classmethod
    def validate_prequal_start(cls, v: str) -> str:
        """Validate prequal start value is 20 digits."""
        if not v.isdigit() or len(v) != 20:
            raise ValueError('Prequal start value must be exactly 20 digits')
        return v


class PathConfig(BaseModel):
    """Configuration for file and directory paths."""
    
    # Input directories
    fullset_requests_dir: Path = Field(default=Path("data/templates/fullset_requests"))
    prequal_requests_dir: Path = Field(default=Path("data/templates/prequal_requests"))
    config_dir: Path = Field(default=Path("config"))
    
    # Output directories  
    output_dir: Path = Field(default=Path("output"))
    reports_dir: Path = Field(default=Path("output/reports"))
    responses_dir: Path = Field(default=Path("output/responses"))
    comparisons_dir: Path = Field(default=Path("output/comparisons"))
    logs_dir: Path = Field(default=Path("output/logs"))
    
    # Data files
    test_data_dir: Path = Field(default=Path("data/test_data"))
    app_ids_file: Path = Field(default=Path("data/test_data/app_ids.json"))
    test_scenarios_file: Path = Field(default=Path("data/test_data/test_scenarios.json"))
    
    @model_validator(mode='after')
    def create_directories(self) -> 'PathConfig':
        """Ensure output directories exist."""
        for field_name, field_value in self.model_dump().items():
            if field_name.endswith('_dir') and isinstance(field_value, Path):
                field_value.mkdir(parents=True, exist_ok=True)
        return self


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    
    level: str = Field(default="INFO", description="Log level")
    enable_console: bool = Field(default=True, description="Enable console logging")
    enable_file: bool = Field(default=True, description="Enable file logging")
    enable_json: bool = Field(default=False, description="Enable JSON log format")
    log_file: Optional[Path] = Field(default=None, description="Log file path")
    max_file_size: int = Field(default=10485760, description="Max log file size in bytes (10MB)")
    backup_count: int = Field(default=5, description="Number of backup log files")
    
    @field_validator('level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()


class ReportConfig(BaseModel):
    """Configuration for report generation."""
    
    enable_html: bool = Field(default=True, description="Enable HTML reports")
    enable_json: bool = Field(default=True, description="Enable JSON reports")
    enable_excel: bool = Field(default=True, description="Enable Excel reports")
    include_charts: bool = Field(default=True, description="Include charts in reports")
    include_performance_metrics: bool = Field(default=True, description="Include performance metrics")
    template_dir: Path = Field(default=Path("templates"), description="Report template directory")
    
    # Chart configuration
    chart_width: int = Field(default=800, ge=400, le=1600, description="Chart width in pixels")
    chart_height: int = Field(default=600, ge=300, le=1200, description="Chart height in pixels")


class Settings(BaseSettings):
    """Main application settings using Pydantic v2."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application metadata
    app_name: str = Field(default="API Test Framework", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Configuration sections
    api: APIEndpointConfig = Field(default_factory=APIEndpointConfig)
    test_execution: TestExecutionConfig = Field(default_factory=TestExecutionConfig)
    app_ids: AppIDConfig = Field(default_factory=AppIDConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    reporting: ReportConfig = Field(default_factory=ReportConfig)
    
    # Runtime settings
    run_id: Optional[str] = Field(default=None, description="Current test run ID")
    correlation_id: Optional[str] = Field(default=None, description="Request correlation ID")
    
    @classmethod
    def from_json_file(cls, config_file: Union[str, Path]) -> 'Settings':
        """Load settings from JSON configuration file."""
        import json
        
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    def to_json_file(self, config_file: Union[str, Path]) -> None:
        """Save current settings to JSON file."""
        import json
        
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self.model_dump(mode='json', exclude={'run_id', 'correlation_id'}),
                    f,
                    indent=2,
                    ensure_ascii=False
                )
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration: {e}")
    
    def get_headers(self) -> Dict[str, str]:
        """Get default HTTP headers."""
        return {
            "Content-Type": "application/json",
            "User-Agent": f"{self.app_name}/{self.app_version}",
            "Host": self.api.host,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        }
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check required directories exist
        required_dirs = [
            self.paths.fullset_requests_dir,
            self.paths.prequal_requests_dir,
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                issues.append(f"Required directory does not exist: {dir_path}")
        
        # Check API configuration
        if not self.api.url:
            issues.append("API URL is required")
        
        if not self.api.host:
            issues.append("API host is required")
        
        return issues
    
    @model_validator(mode='after')
    def validate_settings(self) -> 'Settings':
        """Post-validation to ensure configuration consistency."""
        # Set log file path if not specified
        if self.logging.enable_file and not self.logging.log_file:
            self.logging.log_file = self.paths.logs_dir / "framework.log"
        
        return self


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(config_file: Optional[Union[str, Path]] = None) -> Settings:
    """Get global settings instance with optional configuration file."""
    global _settings
    
    if _settings is None:
        if config_file:
            _settings = Settings.from_json_file(config_file)
        else:
            # Try to load from default location
            default_config = Path("config/settings.json")
            if default_config.exists():
                _settings = Settings.from_json_file(default_config)
            else:
                _settings = Settings()
    
    return _settings


def reload_settings(config_file: Optional[Union[str, Path]] = None) -> Settings:
    """Reload settings from configuration file."""
    global _settings
    _settings = None
    return get_settings(config_file)


def create_default_config(config_file: Union[str, Path]) -> None:
    """Create a default configuration file."""
    default_settings = Settings()
    default_settings.to_json_file(config_file)