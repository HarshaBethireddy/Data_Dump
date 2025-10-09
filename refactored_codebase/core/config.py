"""
Enterprise-grade configuration management system.

Provides centralized, environment-aware configuration management with
validation, type safety, and flexible loading strategies.
"""

import os
import csv
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass(frozen=True)
class APIConfiguration:
    """Immutable API configuration settings."""
    url: str
    host: str
    timeout: int = 30
    verify_ssl: bool = False
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.url or not self.host:
            raise ValueError("URL and host are required")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")


@dataclass(frozen=True)
class TestConfiguration:
    """Test execution configuration settings."""
    parallel_count: int = 2
    think_time: float = 3.0
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self) -> None:
        """Validate test configuration."""
        if self.parallel_count <= 0:
            raise ValueError("Parallel count must be positive")
        if self.think_time < 0:
            raise ValueError("Think time cannot be negative")


@dataclass(frozen=True)
class PathConfiguration:
    """Path configuration for directories and files."""
    # Input directories
    fullset_request_dir: Path = field(default_factory=lambda: Path("data/requests/fullset"))
    prequal_request_dir: Path = field(default_factory=lambda: Path("data/requests/prequal"))
    
    # Output directories  
    json_output_dir: Path = field(default_factory=lambda: Path("output/json"))
    test_response_dir: Path = field(default_factory=lambda: Path("output/responses"))
    report_dir: Path = field(default_factory=lambda: Path("output/reports"))
    comparison_dir: Path = field(default_factory=lambda: Path("output/comparisons"))
    merged_output_dir: Path = field(default_factory=lambda: Path("output/merged"))
    
    # Data files
    master_testdata_file: Path = field(default_factory=lambda: Path("data/testdata/MasterTestdata.xlsx"))
    prequal_testdata_file: Path = field(default_factory=lambda: Path("data/testdata/PreQual_MasterTestdata.xlsx"))
    
    def __post_init__(self) -> None:
        """Convert string paths to Path objects if needed."""
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, str):
                object.__setattr__(self, field_name, Path(field_value))


class ConfigurationLoader(ABC):
    """Abstract base class for configuration loaders."""
    
    @abstractmethod
    def load(self, source: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from source."""
        pass


class CSVConfigurationLoader(ConfigurationLoader):
    """Load configuration from CSV files."""
    
    def load(self, source: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from CSV file."""
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {source_path}")
        
        try:
            with open(source_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                return next(reader)
        except Exception as e:
            raise RuntimeError(f"Failed to load CSV configuration: {e}") from e


class JSONConfigurationLoader(ConfigurationLoader):
    """Load configuration from JSON files."""
    
    def load(self, source: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {source_path}")
        
        try:
            with open(source_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            raise RuntimeError(f"Failed to load JSON configuration: {e}") from e


class EnvironmentConfigurationLoader(ConfigurationLoader):
    """Load configuration from environment variables."""
    
    def load(self, source: Union[str, Path] = None) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            'API_URL': os.getenv('API_URL', ''),
            'Host': os.getenv('API_HOST', ''),
            'timeout': int(os.getenv('API_TIMEOUT', '30')),
            'verify_ssl': os.getenv('API_VERIFY_SSL', 'false').lower() == 'true'
        }


class ConfigurationManager:
    """
    Enterprise-grade configuration manager with multiple loading strategies.
    
    Supports loading from CSV, JSON, environment variables, and provides
    validation, caching, and environment-specific configurations.
    """
    
    def __init__(self, 
                 config_file: Optional[Union[str, Path]] = None,
                 environment: str = "development"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
            environment: Environment name (development, testing, production)
        """
        self.environment = environment
        self.config_file = self._resolve_config_file(config_file)
        self._loader = self._create_loader()
        
        # Load configurations
        self._api_config: Optional[APIConfiguration] = None
        self._test_config = TestConfiguration()
        self._path_config = PathConfiguration()
        
    def _resolve_config_file(self, config_file: Optional[Union[str, Path]]) -> Optional[Path]:
        """Resolve configuration file path with fallbacks."""
        if config_file:
            return Path(config_file)
        
        # Try environment-specific config files
        possible_configs = [
            Path(f"config/{self.environment}.json"),
            Path(f"config/{self.environment}.csv"),
            Path("config/api_config.json"),
            Path("config/api_config.csv"),
            Path("api_config.json"),
            Path("api_config.csv")
        ]
        
        for config_path in possible_configs:
            if config_path.exists():
                return config_path
        
        return None
    
    def _create_loader(self) -> ConfigurationLoader:
        """Create appropriate configuration loader based on file type."""
        if not self.config_file:
            return EnvironmentConfigurationLoader()
        
        suffix = self.config_file.suffix.lower()
        if suffix == '.csv':
            return CSVConfigurationLoader()
        elif suffix == '.json':
            return JSONConfigurationLoader()
        else:
            raise ValueError(f"Unsupported configuration file type: {suffix}")
    
    @property
    def api_config(self) -> APIConfiguration:
        """Get API configuration, loading if necessary."""
        if self._api_config is None:
            self._load_api_config()
        return self._api_config
    
    @property
    def test_config(self) -> TestConfiguration:
        """Get test configuration."""
        return self._test_config
    
    @property
    def path_config(self) -> PathConfiguration:
        """Get path configuration."""
        return self._path_config
    
    def _load_api_config(self) -> None:
        """Load API configuration from configured source."""
        try:
            config_data = self._loader.load(self.config_file)
            
            # Map configuration keys (handle different naming conventions)
            api_url = config_data.get('API_URL') or config_data.get('url', '')
            host = config_data.get('Host') or config_data.get('host', '')
            timeout = int(config_data.get('timeout', 30))
            verify_ssl = str(config_data.get('verify_ssl', 'false')).lower() == 'true'
            
            self._api_config = APIConfiguration(
                url=api_url,
                host=host,
                timeout=timeout,
                verify_ssl=verify_ssl
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to load API configuration: {e}") from e
    
    def get_headers(self) -> Dict[str, str]:
        """Get default HTTP headers for API requests."""
        return {
            "Content-Type": "application/json",
            "User-Agent": "APITestFramework/2.0",
            "Host": self.api_config.host,
            "Accept": "application/json"
        }
    
    def validate_paths(self) -> None:
        """Validate that required input paths exist."""
        required_paths = [
            self.path_config.fullset_request_dir,
            self.path_config.prequal_request_dir
        ]
        
        missing_paths = [path for path in required_paths if not path.exists()]
        if missing_paths:
            raise FileNotFoundError(f"Required directories not found: {missing_paths}")
    
    def ensure_output_directories(self) -> None:
        """Ensure all output directories exist."""
        output_dirs = [
            self.path_config.json_output_dir,
            self.path_config.test_response_dir,
            self.path_config.report_dir,
            self.path_config.comparison_dir,
            self.path_config.merged_output_dir
        ]
        
        for directory in output_dirs:
            directory.mkdir(parents=True, exist_ok=True)
    
    def reload(self) -> None:
        """Reload configuration from source."""
        self._api_config = None
        self._load_api_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary for debugging/logging."""
        return {
            'environment': self.environment,
            'config_file': str(self.config_file) if self.config_file else None,
            'api_config': {
                'url': self.api_config.url,
                'host': self.api_config.host,
                'timeout': self.api_config.timeout,
                'verify_ssl': self.api_config.verify_ssl
            },
            'test_config': {
                'parallel_count': self.test_config.parallel_count,
                'think_time': self.test_config.think_time
            }
        }