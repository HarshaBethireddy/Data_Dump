"""
Centralized settings management using Pydantic Settings.

This module provides environment-aware configuration management with
validation, type safety, and support for multiple configuration sources.
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
from functools import lru_cache

from pydantic import BaseSettings, Field, validator
from pydantic.env_settings import SettingsSourceCallable

from refactored_codebase.config.models import (
    APIConfig,
    TestConfig,
    PathConfig,
    AppIDConfig,
    LoggingConfig,
    DatabaseConfig,
    Environment
)


class Settings(BaseSettings):
    """
    Main settings class that aggregates all configuration models.
    
    Supports multiple configuration sources:
    1. Environment variables
    2. JSON configuration files
    3. Default values
    """
    
    # Environment settings
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Current environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Configuration models
    api: APIConfig = Field(default_factory=APIConfig, description="API configuration")
    test: TestConfig = Field(default_factory=TestConfig, description="Test configuration")
    paths: PathConfig = Field(default_factory=PathConfig, description="Path configuration")
    appid: AppIDConfig = Field(default_factory=AppIDConfig, description="APPID configuration")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="Database configuration")
    
    # Framework metadata
    framework_name: str = Field(default="Enterprise API Testing Framework", description="Framework name")
    framework_version: str = Field(default="2.0.0", description="Framework version")
    
    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False
        validate_assignment = True
        extra = "forbid"
        
        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            """Customize settings sources priority."""
            return (
                init_settings,
                json_config_settings_source,
                env_settings,
                file_secret_settings,
            )
    
    def __init__(self, **kwargs):
        """Initialize settings and ensure directories exist."""
        super().__init__(**kwargs)
        self.paths.ensure_directories()
    
    @validator('environment', pre=True)
    def validate_environment(cls, v):
        """Validate and normalize environment value."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
    def get_config_file_path(self) -> Path:
        """Get the configuration file path for current environment."""
        return self.paths.config_dir / f"{self.environment.value}.json"
    
    def save_to_file(self, file_path: Optional[Path] = None) -> None:
        """Save current settings to JSON file."""
        if file_path is None:
            file_path = self.get_config_file_path()
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.dict(), f, indent=2, default=str)
    
    def load_from_file(self, file_path: Path) -> Dict[str, Any]:
        """Load settings from JSON file."""
        if not file_path.exists():
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_headers(self) -> Dict[str, str]:
        """Get default HTTP headers for API requests."""
        return {
            "Content-Type": "application/json",
            "User-Agent": f"{self.framework_name}/{self.framework_version}",
            "Host": self.api.host,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION


def json_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    Custom settings source that loads configuration from JSON files.
    
    Loads configuration in the following order:
    1. Environment-specific config (e.g., development.json)
    2. Default config (default.json)
    """
    config_data = {}
    
    # Get environment from settings or environment variable
    env = getattr(settings, 'environment', None)
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development').lower()
    
    config_dir = Path("config")
    
    # Load default configuration
    default_config_path = config_dir / "default.json"
    if default_config_path.exists():
        try:
            with open(default_config_path, 'r', encoding='utf-8') as f:
                config_data.update(json.load(f))
        except (json.JSONDecodeError, IOError):
            pass  # Ignore errors in default config
    
    # Load environment-specific configuration
    env_config_path = config_dir / f"{env}.json"
    if env_config_path.exists():
        try:
            with open(env_config_path, 'r', encoding='utf-8') as f:
                env_config = json.load(f)
                # Deep merge environment config over default config
                config_data.update(env_config)
        except (json.JSONDecodeError, IOError):
            pass  # Ignore errors in environment config
    
    return config_data


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function uses LRU cache to ensure settings are loaded only once
    and reused throughout the application lifecycle.
    """
    return Settings()


def create_default_configs() -> None:
    """Create default configuration files if they don't exist."""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Default configuration
    default_config = {
        "environment": "development",
        "debug": True,
        "api": {
            "url": "http://localhost:8080/api",
            "host": "localhost:8080",
            "timeout": 30,
            "verify_ssl": False,
            "max_retries": 3,
            "retry_delay": 1.0
        },
        "test": {
            "parallel_count": 2,
            "think_time": 3.0,
            "batch_size": 100,
            "enable_comparison": True
        },
        "appid": {
            "start_range": 100000000,
            "end_range": 999999999,
            "prequal_start_range": 10000000000000000000,
            "prequal_end_range": 99999999999999999999,
            "increment": 1
        },
        "logging": {
            "level": "INFO",
            "file_rotation": True,
            "max_file_size": "10MB",
            "backup_count": 5
        }
    }
    
    default_config_path = config_dir / "default.json"
    if not default_config_path.exists():
        with open(default_config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
    
    # Development configuration
    dev_config = {
        "environment": "development",
        "debug": True,
        "api": {
            "url": "http://10.31.211.141:9080/IBService?workflow=InboundJSONCPF",
            "host": "10.31.211.141:9080"
        },
        "logging": {
            "level": "DEBUG"
        }
    }
    
    dev_config_path = config_dir / "development.json"
    if not dev_config_path.exists():
        with open(dev_config_path, 'w', encoding='utf-8') as f:
            json.dump(dev_config, f, indent=2)
    
    # Production configuration template
    prod_config = {
        "environment": "production",
        "debug": False,
        "api": {
            "verify_ssl": True,
            "timeout": 60
        },
        "test": {
            "parallel_count": 5,
            "batch_size": 500
        },
        "logging": {
            "level": "INFO",
            "file_rotation": True
        }
    }
    
    prod_config_path = config_dir / "production.json"
    if not prod_config_path.exists():
        with open(prod_config_path, 'w', encoding='utf-8') as f:
            json.dump(prod_config, f, indent=2)


if __name__ == "__main__":
    # Create default configuration files
    create_default_configs()
    print("✅ Default configuration files created!")