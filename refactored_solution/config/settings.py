"""
Configuration management for the API testing framework.
"""
import os
import csv
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class APIConfig:
    """API configuration settings."""
    url: str
    host: str
    timeout: int = 30
    verify_ssl: bool = False


@dataclass
class TestConfig:
    """Test execution configuration."""
    parallel_count: int = 2
    think_time: float = 3.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class PathConfig:
    """Path configuration for folders and files."""
    json_folder: str = "json_files"
    test_response_folder: str = "TestResponse"
    report_folder: str = "Report"
    compare_result_folder: str = "CompareResult"
    merged_output_folder: str = "MergedOut_File"
    
    # Source folders
    fullset_request_folder: str = "FullSetRequest"
    prequal_request_folder: str = "Prequal Request"
    
    # Excel files
    master_testdata_file: str = "MasterTestdata.xlsx"
    prequal_testdata_file: str = "PreQual_MasterTestdata.xlsx"


class ConfigManager:
    """Centralized configuration manager."""
    
    def __init__(self, config_file: str = "api_config.csv"):
        self.config_file = config_file
        self.api_config = self._load_api_config()
        self.test_config = TestConfig()
        self.path_config = PathConfig()
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration from CSV file."""
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"Configuration file {self.config_file} not found")
            
            with open(self.config_file, 'r') as file:
                reader = csv.DictReader(file)
                row = next(reader)
                return APIConfig(
                    url=row['API_URL'],
                    host=row['Host']
                )
        except Exception as e:
            raise RuntimeError(f"Failed to load API configuration: {e}")
    
    def get_headers(self) -> Dict[str, str]:
        """Get default headers for API requests."""
        return {
            "Content-Type": "application/json",
            "User-Agent": "APITestFramework/2.0",
            "Host": self.api_config.host
        }
    
    def validate_paths(self) -> None:
        """Validate that required paths exist."""
        required_paths = [
            self.path_config.fullset_request_folder,
            self.path_config.prequal_request_folder
        ]
        
        missing_paths = [path for path in required_paths if not os.path.exists(path)]
        if missing_paths:
            raise FileNotFoundError(f"Required folders not found: {missing_paths}")
    
    def ensure_output_directories(self) -> None:
        """Ensure all output directories exist."""
        output_dirs = [
            self.path_config.json_folder,
            self.path_config.test_response_folder,
            self.path_config.report_folder,
            self.path_config.compare_result_folder,
            self.path_config.merged_output_folder
        ]
        
        for directory in output_dirs:
            os.makedirs(directory, exist_ok=True)


# Global configuration instance
config = ConfigManager()