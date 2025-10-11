"""
Configuration management using Pydantic V2 with JSON file loading.

This module provides centralized configuration management with validation,
type safety, and easy loading from JSON configuration files.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from apitesting.core.models import (
    APIConfig,
    ApplicationConfig,
    LoggingConfig,
    PathsConfig,
    ReportsConfig,
    TestDataConfig,
    TestExecutionConfig
)
from apitesting.core.exceptions import ConfigurationError
from apitesting.utils.validators import PathValidator


class Settings(BaseSettings):
    """
    Application settings loaded from JSON configuration file.
    
    This class uses Pydantic V2 for validation and type safety.
    Configuration can be loaded from a JSON file or environment variables.
    """
    
    model_config = SettingsConfigDict(
        json_file="config.json",
        json_file_encoding="utf-8",
        case_sensitive=False,
        validate_default=True,
        extra="ignore"
    )
    
    api: APIConfig
    test_execution: TestExecutionConfig
    test_data: TestDataConfig
    paths: PathsConfig
    logging: LoggingConfig
    reports: ReportsConfig
    
    _config_file_path: Optional[Path] = None
    
    @classmethod
    def from_json_file(cls, config_file: Path) -> "Settings":
        """
        Load settings from a JSON configuration file.
        
        Args:
            config_file: Path to JSON configuration file
            
        Returns:
            Settings instance with loaded configuration
            
        Raises:
            ConfigurationError: If configuration cannot be loaded or is invalid
        """
        try:
            # Validate file exists
            config_file = PathValidator.validate_file_exists(
                config_file,
                "Configuration file"
            )
            
            # Read JSON file
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Create settings instance
            settings = cls(**config_data)
            settings._config_file_path = config_file
            
            return settings
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file: {config_file}",
                config_key="json_file",
                details={"error": str(e), "line": e.lineno, "column": e.colno},
                original_error=e
            )
        except FileNotFoundError as e:
            raise ConfigurationError(
                f"Configuration file not found: {config_file}",
                config_key="config_file",
                original_error=e
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration from {config_file}",
                config_key="config_file",
                original_error=e
            )
    
    def validate_paths(self) -> None:
        """
        Validate that all configured paths exist and are accessible.
        
        Raises:
            ConfigurationError: If any path validation fails
        """
        # Validate input template directories
        try:
            PathValidator.validate_directory_exists(
                self.paths.input_templates_regular,
                "Regular templates directory"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Invalid regular templates path: {self.paths.input_templates_regular}",
                config_key="paths.input_templates_regular",
                original_error=e
            )
        
        try:
            PathValidator.validate_directory_exists(
                self.paths.input_templates_prequal,
                "Prequal templates directory"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Invalid prequal templates path: {self.paths.input_templates_prequal}",
                config_key="paths.input_templates_prequal",
                original_error=e
            )
        
        # Validate input test data files
        try:
            PathValidator.validate_file_exists(
                self.paths.input_test_data_regular,
                "Regular test data file"
            )
            PathValidator.validate_file_extension(
                self.paths.input_test_data_regular,
                ".xlsx"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Invalid regular test data file: {self.paths.input_test_data_regular}",
                config_key="paths.input_test_data_regular",
                original_error=e
            )
        
        try:
            PathValidator.validate_file_exists(
                self.paths.input_test_data_prequal,
                "Prequal test data file"
            )
            PathValidator.validate_file_extension(
                self.paths.input_test_data_prequal,
                ".xlsx"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Invalid prequal test data file: {self.paths.input_test_data_prequal}",
                config_key="paths.input_test_data_prequal",
                original_error=e
            )
    
    def ensure_output_directories(self) -> None:
        """
        Ensure all output directories exist, creating them if necessary.
        
        Raises:
            ConfigurationError: If directories cannot be created
        """
        output_paths = [
            self.paths.output_responses,
            self.paths.output_reports,
            self.paths.output_comparisons,
            self.paths.output_processed,
            self.paths.logs
        ]
        
        for output_path in output_paths:
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to create output directory: {output_path}",
                    config_key="paths",
                    details={"path": str(output_path)},
                    original_error=e
                )
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Host": self.api.host
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary.
        
        Returns:
            Dictionary representation of settings
        """
        return {
            "api": self.api.model_dump(),
            "test_execution": self.test_execution.model_dump(),
            "test_data": self.test_data.model_dump(),
            "paths": {
                k: str(v) for k, v in self.paths.model_dump().items()
            },
            "logging": self.logging.model_dump(),
            "reports": self.reports.model_dump()
        }
    
    def to_json(self, indent: int = 4) -> str:
        """
        Convert settings to JSON string.
        
        Args:
            indent: JSON indentation
            
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def save_to_file(self, output_file: Path) -> None:
        """
        Save current settings to a JSON file.
        
        Args:
            output_file: Path to output file
            
        Raises:
            ConfigurationError: If settings cannot be saved
        """
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save configuration to {output_file}",
                config_key="output_file",
                original_error=e
            )
    
    @property
    def config_file_path(self) -> Optional[Path]:
        """Get the path to the configuration file that was loaded."""
        return self._config_file_path


class ConfigurationManager:
    """
    Singleton configuration manager for the application.
    
    Provides centralized access to application configuration.
    """
    
    _instance: Optional["ConfigurationManager"] = None
    _settings: Optional[Settings] = None
    
    def __new__(cls) -> "ConfigurationManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration manager."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
    
    def load_config(
        self,
        config_file: Optional[Path] = None,
        validate_paths: bool = True,
        ensure_output_dirs: bool = True
    ) -> Settings:
        """
        Load configuration from file.
        
        Args:
            config_file: Path to configuration file (defaults to config.json)
            validate_paths: Whether to validate input paths exist
            ensure_output_dirs: Whether to create output directories
            
        Returns:
            Loaded settings
            
        Raises:
            ConfigurationError: If configuration cannot be loaded
        """
        if config_file is None:
            # Look for config.json in current directory or refactored_codebase
            candidates = [
                Path("config.json"),
                Path("refactored_codebase/config.json"),
                Path(__file__).parent.parent / "config.json"
            ]
            
            for candidate in candidates:
                if candidate.exists():
                    config_file = candidate
                    break
            
            if config_file is None:
                raise ConfigurationError(
                    "Configuration file not found. Please provide config.json",
                    config_key="config_file",
                    details={"searched_locations": [str(c) for c in candidates]}
                )
        
        # Load settings
        self._settings = Settings.from_json_file(Path(config_file))
        
        # Validate paths if requested
        if validate_paths:
            self._settings.validate_paths()
        
        # Ensure output directories if requested
        if ensure_output_dirs:
            self._settings.ensure_output_directories()
        
        return self._settings
    
    def get_settings(self) -> Settings:
        """
        Get current settings.
        
        Returns:
            Current settings instance
            
        Raises:
            ConfigurationError: If settings not loaded
        """
        if self._settings is None:
            raise ConfigurationError(
                "Configuration not loaded. Call load_config() first.",
                config_key="settings"
            )
        return self._settings
    
    def reload_config(self) -> Settings:
        """
        Reload configuration from the original file.
        
        Returns:
            Reloaded settings
            
        Raises:
            ConfigurationError: If configuration cannot be reloaded
        """
        if self._settings is None or self._settings.config_file_path is None:
            raise ConfigurationError(
                "No configuration file to reload from",
                config_key="config_file"
            )
        
        return self.load_config(self._settings.config_file_path)
    
    def update_config(self, **kwargs) -> Settings:
        """
        Update specific configuration values.
        
        Args:
            **kwargs: Configuration values to update
            
        Returns:
            Updated settings
            
        Raises:
            ConfigurationError: If update fails
        """
        if self._settings is None:
            raise ConfigurationError(
                "Configuration not loaded. Call load_config() first.",
                config_key="settings"
            )
        
        try:
            # Get current config as dict
            config_dict = self._settings.to_dict()
            
            # Update with new values
            for key, value in kwargs.items():
                if '.' in key:
                    # Handle nested keys like "api.timeout"
                    parts = key.split('.')
                    current = config_dict
                    for part in parts[:-1]:
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    config_dict[key] = value
            
            # Create new settings instance
            self._settings = Settings(**config_dict)
            
            return self._settings
            
        except Exception as e:
            raise ConfigurationError(
                "Failed to update configuration",
                config_key="update",
                details={"updates": kwargs},
                original_error=e
            )


# Global configuration manager instance
_config_manager = ConfigurationManager()


def load_config(
    config_file: Optional[Path] = None,
    validate_paths: bool = True,
    ensure_output_dirs: bool = True
) -> Settings:
    """
    Load application configuration.
    
    Args:
        config_file: Path to configuration file
        validate_paths: Whether to validate input paths
        ensure_output_dirs: Whether to create output directories
        
    Returns:
        Loaded settings
    """
    return _config_manager.load_config(config_file, validate_paths, ensure_output_dirs)


def get_config() -> Settings:
    """
    Get current application configuration.
    
    Returns:
        Current settings instance
    """
    return _config_manager.get_settings()


def reload_config() -> Settings:
    """
    Reload configuration from file.
    
    Returns:
        Reloaded settings
    """
    return _config_manager.reload_config()


def update_config(**kwargs) -> Settings:
    """
    Update configuration values.
    
    Args:
        **kwargs: Configuration values to update
        
    Returns:
        Updated settings
    """
    return _config_manager.update_config(**kwargs)


# Example usage
if __name__ == "__main__":
    # Load configuration
    config = load_config(Path("config.json"))
    
    # Access configuration values
    print(f"API URL: {config.api.url}")
    print(f"Parallel Workers: {config.test_execution.parallel_workers}")
    print(f"Log Level: {config.logging.level}")
    
    # Get headers
    headers = config.get_headers()
    print(f"Headers: {headers}")
    
    # Save configuration
    config.save_to_file(Path("config_backup.json"))