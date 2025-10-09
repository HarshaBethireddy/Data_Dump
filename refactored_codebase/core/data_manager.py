"""
Modern test data management system.

This module provides enterprise-grade test data management with support for
JSON templates, APPID injection, and data validation.
"""

import json
import re
from typing import Dict, Any, List, Optional, Iterator, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from refactored_codebase.core.appid_manager import AppIDManager
from refactored_codebase.config.models import PathConfig
from refactored_codebase.utils.logging import get_logger


class DataType(str, Enum):
    """Test data types."""
    REGULAR = "regular"
    PREQUAL = "prequal"
    BOTH = "both"


@dataclass
class TestDataFile:
    """Test data file metadata."""
    file_path: Path
    file_name: str
    data_type: DataType
    template_data: Dict[str, Any]
    appid_placeholder: str = "$APPID"
    
    def __post_init__(self):
        """Validate file exists and load template data."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Test data file not found: {self.file_path}")


@dataclass
class ProcessedTestData:
    """Processed test data with injected APPID."""
    file_name: str
    appid: int
    data: Dict[str, Any]
    data_type: DataType
    original_file: Path


class TestDataManager:
    """
    Enterprise test data manager.
    
    Features:
    - JSON template processing with APPID injection
    - Support for regular and prequal data types
    - Batch processing capabilities
    - Data validation and error handling
    - Flexible template system
    """
    
    def __init__(self, paths: PathConfig, appid_manager: AppIDManager):
        """
        Initialize test data manager.
        
        Args:
            paths: Path configuration
            appid_manager: APPID manager instance
        """
        self.paths = paths
        self.appid_manager = appid_manager
        self.logger = get_logger(self.__class__.__name__)
        
        # Data type to directory mapping
        self.data_directories = {
            DataType.REGULAR: self.paths.requests_dir / "fullset",
            DataType.PREQUAL: self.paths.requests_dir / "prequal"
        }
        
        self.logger.info("Test Data Manager initialized")
    
    def _load_json_template(self, file_path: Path) -> Dict[str, Any]:
        """
        Load JSON template from file.
        
        Args:
            file_path: Path to JSON template file
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If JSON is invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load {file_path}: {e}") from e
    
    def _inject_appid(self, data: Dict[str, Any], appid: int, placeholder: str = "$APPID") -> Dict[str, Any]:
        """
        Inject APPID into JSON data recursively.
        
        Args:
            data: JSON data
            appid: APPID to inject
            placeholder: APPID placeholder string
            
        Returns:
            JSON data with APPID injected
        """
        def replace_recursive(obj):
            if isinstance(obj, dict):
                return {key: replace_recursive(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [replace_recursive(item) for item in obj]
            elif isinstance(obj, str):
                return obj.replace(placeholder, str(appid))
            else:
                return obj
        
        return replace_recursive(data)
    
    def _validate_template(self, template_data: Dict[str, Any], data_type: DataType) -> bool:
        """
        Validate template data structure.
        
        Args:
            template_data: Template data to validate
            data_type: Type of data (regular/prequal)
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic structure validation
            if not isinstance(template_data, dict):
                return False
            
            # Check for required APPID placeholder
            json_str = json.dumps(template_data)
            if "$APPID" not in json_str:
                self.logger.warning("Template does not contain $APPID placeholder")
            
            # Data type specific validation
            if data_type == DataType.PREQUAL:
                # Check for prequal-specific structure
                if "PREQUAL" not in template_data:
                    self.logger.warning("Prequal template missing PREQUAL root element")
            elif data_type == DataType.REGULAR:
                # Check for regular application structure
                if "APPLICATION" not in template_data:
                    self.logger.warning("Regular template missing APPLICATION root element")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Template validation error: {e}")
            return False
    
    def discover_templates(self, data_type: DataType) -> List[TestDataFile]:
        """
        Discover JSON template files in the specified directory.
        
        Args:
            data_type: Type of data to discover
            
        Returns:
            List of discovered template files
        """
        if data_type not in self.data_directories:
            raise ValueError(f"Unknown data type: {data_type}")
        
        directory = self.data_directories[data_type]
        if not directory.exists():
            self.logger.warning(f"Data directory does not exist: {directory}")
            return []
        
        templates = []
        json_files = list(directory.glob("*.json"))
        
        self.logger.info(f"Discovering templates in {directory} - found {len(json_files)} files")
        
        for json_file in json_files:
            try:
                template_data = self._load_json_template(json_file)
                
                if self._validate_template(template_data, data_type):
                    template = TestDataFile(
                        file_path=json_file,
                        file_name=json_file.name,
                        data_type=data_type,
                        template_data=template_data
                    )
                    templates.append(template)
                    self.logger.debug(f"Loaded template: {json_file.name}")
                else:
                    self.logger.warning(f"Invalid template skipped: {json_file.name}")
                    
            except Exception as e:
                self.logger.error(f"Failed to load template {json_file.name}: {e}")
        
        self.logger.info(f"Discovered {len(templates)} valid templates for {data_type}")
        return templates
    
    def process_template(self, template: TestDataFile, appid: Optional[int] = None) -> ProcessedTestData:
        """
        Process a single template with APPID injection.
        
        Args:
            template: Template file to process
            appid: Specific APPID to use (if None, generates new one)
            
        Returns:
            Processed test data
        """
        # Generate APPID if not provided
        if appid is None:
            if template.data_type == DataType.PREQUAL:
                appid = self.appid_manager.get_next_prequal_appid()
            else:
                appid = self.appid_manager.get_next_regular_appid()
        
        # Inject APPID into template
        processed_data = self._inject_appid(template.template_data, appid)
        
        self.logger.debug(f"Processed template {template.file_name} with APPID {appid}")
        
        return ProcessedTestData(
            file_name=template.file_name,
            appid=appid,
            data=processed_data,
            data_type=template.data_type,
            original_file=template.file_path
        )
    
    def process_templates_batch(
        self, 
        templates: List[TestDataFile], 
        appid_list: Optional[List[int]] = None
    ) -> Iterator[ProcessedTestData]:
        """
        Process multiple templates in batch.
        
        Args:
            templates: List of templates to process
            appid_list: Optional list of specific APPIDs to use
            
        Yields:
            Processed test data
        """
        if appid_list and len(appid_list) != len(templates):
            raise ValueError("APPID list length must match templates length")
        
        for i, template in enumerate(templates):
            appid = appid_list[i] if appid_list else None
            yield self.process_template(template, appid)
    
    def process_data_type(self, data_type: DataType, count: Optional[int] = None) -> Iterator[ProcessedTestData]:
        """
        Process all templates of a specific data type.
        
        Args:
            data_type: Type of data to process
            count: Maximum number of templates to process
            
        Yields:
            Processed test data
        """
        templates = self.discover_templates(data_type)
        
        if count:
            templates = templates[:count]
        
        self.logger.info(f"Processing {len(templates)} templates for {data_type}")
        
        for template in templates:
            yield self.process_template(template)
    
    def save_processed_data(self, processed_data: ProcessedTestData, output_dir: Path) -> Path:
        """
        Save processed data to file.
        
        Args:
            processed_data: Processed test data
            output_dir: Output directory
            
        Returns:
            Path to saved file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with APPID
        base_name = processed_data.file_name.replace('.json', '')
        output_filename = f"{base_name}_{processed_data.appid}.json"
        output_path = output_dir / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data.data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved processed data to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to save processed data: {e}")
            raise
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about available templates."""
        stats = {}
        
        for data_type in [DataType.REGULAR, DataType.PREQUAL]:
            templates = self.discover_templates(data_type)
            stats[data_type.value] = {
                "count": len(templates),
                "files": [t.file_name for t in templates],
                "directory": str(self.data_directories[data_type])
            }
        
        return stats
    
    def validate_all_templates(self) -> Dict[str, List[str]]:
        """
        Validate all discovered templates.
        
        Returns:
            Dictionary with valid and invalid template lists
        """
        results = {"valid": [], "invalid": []}
        
        for data_type in [DataType.REGULAR, DataType.PREQUAL]:
            directory = self.data_directories[data_type]
            if not directory.exists():
                continue
            
            for json_file in directory.glob("*.json"):
                try:
                    template_data = self._load_json_template(json_file)
                    if self._validate_template(template_data, data_type):
                        results["valid"].append(str(json_file))
                    else:
                        results["invalid"].append(str(json_file))
                except Exception:
                    results["invalid"].append(str(json_file))
        
        return results