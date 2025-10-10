"""
Test data preparation service with APPID generation and JSON template processing.

This service handles:
- APPID range generation (regular and prequal)
- JSON template processing with APPID replacement
- Test data file management
"""

import logging
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Union

from ..config.settings import get_config
from ..core.constants import APPID_PLACEHOLDER, EXCEL_APPID_COLUMN, EXCEL_DATA_START_ROW
from ..core.exceptions import (
    AppIDGenerationError,
    TestDataPreparationError,
    ExcelProcessingError
)
from ..core.models import AppIDRange, TestDataFile, TestDataType
from ..utils.file_handler import FileHandler, JSONHandler, ExcelHandler
from ..utils.logger import get_logger, PerformanceLogger
from ..utils.validators import AppIDValidator


class AppIDGenerator:
    """
    Generates APPID sequences for test data.
    
    Supports both regular integer APPIDs and 20-digit prequal APPIDs.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize APPID generator.
        
        Args:
            logger: Logger instance (creates new one if not provided)
        """
        self.logger = logger or get_logger(__name__)
    
    def generate_regular_appids(
        self,
        start_value: int,
        count: int,
        increment: int = 1
    ) -> List[int]:
        """
        Generate regular integer APPIDs.
        
        Args:
            start_value: Starting APPID value
            count: Number of APPIDs to generate
            increment: Increment between APPIDs
            
        Returns:
            List of generated APPIDs
            
        Raises:
            AppIDGenerationError: If generation fails
        """
        try:
            # Validate parameters
            AppIDValidator.validate_appid_range(
                start_value=start_value,
                increment=increment,
                count=count,
                is_prequal=False
            )
            
            # Generate APPIDs
            appids = []
            current = start_value
            
            for i in range(count):
                appids.append(current)
                current += increment
            
            self.logger.info(
                f"Generated {count} regular APPIDs",
                extra={
                    "start": start_value,
                    "end": appids[-1],
                    "increment": increment
                }
            )
            
            return appids
            
        except Exception as e:
            raise AppIDGenerationError(
                "Failed to generate regular APPIDs",
                start_value=start_value,
                increment=increment,
                count=count,
                original_error=e
            )
    
    def generate_prequal_appids(
        self,
        start_value: str,
        count: int,
        increment: int = 1
    ) -> List[str]:
        """
        Generate prequal 20-digit APPIDs.
        
        Args:
            start_value: Starting APPID value (20-digit string)
            count: Number of APPIDs to generate
            increment: Increment between APPIDs
            
        Returns:
            List of generated APPIDs as 20-digit strings
            
        Raises:
            AppIDGenerationError: If generation fails
        """
        try:
            # Validate parameters
            AppIDValidator.validate_appid_range(
                start_value=start_value,
                increment=increment,
                count=count,
                is_prequal=True
            )
            
            # Generate APPIDs using Decimal for precision
            appids = []
            current = Decimal(start_value)
            
            for i in range(count):
                # Format as 20-digit string with leading zeros
                appid_str = f"{int(current):020d}"
                appids.append(appid_str)
                current += Decimal(increment)
            
            self.logger.info(
                f"Generated {count} prequal APPIDs",
                extra={
                    "start": start_value,
                    "end": appids[-1],
                    "increment": increment
                }
            )
            
            return appids
            
        except Exception as e:
            raise AppIDGenerationError(
                "Failed to generate prequal APPIDs",
                start_value=start_value,
                increment=increment,
                count=count,
                original_error=e
            )
    
    def generate_from_range(self, appid_range: AppIDRange) -> List[Union[int, str]]:
        """
        Generate APPIDs from an AppIDRange configuration.
        
        Args:
            appid_range: APPID range configuration
            
        Returns:
            List of generated APPIDs
            
        Raises:
            AppIDGenerationError: If generation fails
        """
        try:
            if appid_range.is_prequal:
                return self.generate_prequal_appids(
                    start_value=str(appid_range.start_value),
                    count=appid_range.count,
                    increment=appid_range.increment
                )
            else:
                return self.generate_regular_appids(
                    start_value=int(appid_range.start_value),
                    count=appid_range.count,
                    increment=appid_range.increment
                )
        except Exception as e:
            raise AppIDGenerationError(
                "Failed to generate APPIDs from range",
                start_value=appid_range.start_value,
                increment=appid_range.increment,
                count=appid_range.count,
                original_error=e
            )


class TestDataProcessor:
    """
    Processes test data templates with APPID values.
    
    Handles JSON template reading, APPID replacement, and file generation.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize test data processor.
        
        Args:
            logger: Logger instance (creates new one if not provided)
        """
        self.logger = logger or get_logger(__name__)
        self.appid_generator = AppIDGenerator(self.logger)
    
    def process_template_with_appid(
        self,
        template_path: Path,
        appid: Union[int, str],
        output_path: Path
    ) -> TestDataFile:
        """
        Process a JSON template file by replacing APPID placeholder.
        
        Args:
            template_path: Path to template file
            appid: APPID value to use
            output_path: Path to save processed file
            
        Returns:
            TestDataFile information
            
        Raises:
            TestDataPreparationError: If processing fails
        """
        try:
            # Read template
            template_data = JSONHandler.read_json(template_path)
            
            # Replace APPID placeholder in the entire JSON structure
            json_str = JSONHandler.write_json.__globals__['json'].dumps(template_data)
            json_str = json_str.replace(APPID_PLACEHOLDER, str(appid))
            processed_data = JSONHandler.read_json.__globals__['json'].loads(json_str)
            
            # Write processed file
            JSONHandler.write_json(output_path, processed_data, indent=4)
            
            self.logger.debug(
                f"Processed template: {template_path.name} with APPID: {appid}"
            )
            
            # Determine data type
            data_type = TestDataType.PREQUAL if isinstance(appid, str) else TestDataType.REGULAR
            
            return TestDataFile(
                file_path=output_path,
                file_type=data_type,
                appid_value=appid,
                processed=True
            )
            
        except Exception as e:
            raise TestDataPreparationError(
                f"Failed to process template: {template_path.name}",
                data_type="prequal" if isinstance(appid, str) else "regular",
                step="template_processing",
                details={"template": str(template_path), "appid": str(appid)},
                original_error=e
            )
    
    def process_templates_batch(
        self,
        template_folder: Path,
        appids: List[Union[int, str]],
        output_folder: Path
    ) -> List[TestDataFile]:
        """
        Process multiple templates with corresponding APPIDs.
        
        Args:
            template_folder: Folder containing template files
            appids: List of APPID values
            output_folder: Folder to save processed files
            
        Returns:
            List of processed test data files
            
        Raises:
            TestDataPreparationError: If batch processing fails
        """
        try:
            # Get template files
            template_files = FileHandler.list_files(template_folder, "*.json")
            
            if not template_files:
                raise TestDataPreparationError(
                    f"No JSON templates found in {template_folder}",
                    data_type="unknown",
                    step="template_discovery"
                )
            
            if len(template_files) != len(appids):
                raise TestDataPreparationError(
                    f"Mismatch: {len(template_files)} templates but {len(appids)} APPIDs",
                    data_type="unknown",
                    step="template_appid_matching",
                    details={
                        "template_count": len(template_files),
                        "appid_count": len(appids)
                    }
                )
            
            # Ensure output folder exists
            FileHandler.ensure_directory(output_folder)
            
            # Process each template
            processed_files = []
            
            for template_file, appid in zip(sorted(template_files), appids):
                output_file = output_folder / template_file.name
                
                test_data_file = self.process_template_with_appid(
                    template_path=template_file,
                    appid=appid,
                    output_path=output_file
                )
                
                processed_files.append(test_data_file)
            
            self.logger.info(
                f"Processed {len(processed_files)} templates successfully"
            )
            
            return processed_files
            
        except Exception as e:
            if isinstance(e, TestDataPreparationError):
                raise
            raise TestDataPreparationError(
                "Failed to process templates batch",
                data_type="unknown",
                step="batch_processing",
                original_error=e
            )


class TestDataService:
    """
    Main service for test data preparation.
    
    Coordinates APPID generation and template processing.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize test data service.
        
        Args:
            logger: Logger instance (creates new one if not provided)
        """
        self.logger = logger or get_logger(__name__)
        self.config = get_config()
        self.appid_generator = AppIDGenerator(self.logger)
        self.processor = TestDataProcessor(self.logger)
    
    def prepare_regular_test_data(
        self,
        template_count: Optional[int] = None
    ) -> List[TestDataFile]:
        """
        Prepare regular test data using configuration.
        
        Args:
            template_count: Number of templates to process (auto-detect if None)
            
        Returns:
            List of processed test data files
            
        Raises:
            TestDataPreparationError: If preparation fails
        """
        try:
            with PerformanceLogger(self.logger, "Prepare Regular Test Data"):
                # Get template folder
                template_folder = self.config.paths.input_templates_regular
                
                # Count templates if not provided
                if template_count is None:
                    templates = FileHandler.list_files(template_folder, "*.json")
                    template_count = len(templates)
                
                if template_count == 0:
                    raise TestDataPreparationError(
                        "No templates found for regular test data",
                        data_type="regular",
                        step="template_counting"
                    )
                
                self.logger.info(f"Preparing {template_count} regular test data files")
                
                # Generate APPIDs
                appids = self.appid_generator.generate_regular_appids(
                    start_value=self.config.test_data.appid_start,
                    count=template_count,
                    increment=self.config.test_data.appid_increment
                )
                
                # Process templates
                processed_files = self.processor.process_templates_batch(
                    template_folder=template_folder,
                    appids=appids,
                    output_folder=self.config.paths.output_processed
                )
                
                self.logger.info(
                    f"Successfully prepared {len(processed_files)} regular test data files"
                )
                
                return processed_files
                
        except Exception as e:
            if isinstance(e, TestDataPreparationError):
                raise
            raise TestDataPreparationError(
                "Failed to prepare regular test data",
                data_type="regular",
                step="preparation",
                original_error=e
            )
    
    def prepare_prequal_test_data(
        self,
        template_count: Optional[int] = None
    ) -> List[TestDataFile]:
        """
        Prepare prequal test data using configuration.
        
        Args:
            template_count: Number of templates to process (auto-detect if None)
            
        Returns:
            List of processed test data files
            
        Raises:
            TestDataPreparationError: If preparation fails
        """
        try:
            with PerformanceLogger(self.logger, "Prepare Prequal Test Data"):
                # Get template folder
                template_folder = self.config.paths.input_templates_prequal
                
                # Count templates if not provided
                if template_count is None:
                    templates = FileHandler.list_files(template_folder, "*.json")
                    template_count = len(templates)
                
                if template_count == 0:
                    raise TestDataPreparationError(
                        "No templates found for prequal test data",
                        data_type="prequal",
                        step="template_counting"
                    )
                
                self.logger.info(f"Preparing {template_count} prequal test data files")
                
                # Generate APPIDs
                appids = self.appid_generator.generate_prequal_appids(
                    start_value=self.config.test_data.prequal_appid_start,
                    count=template_count,
                    increment=self.config.test_data.prequal_appid_increment
                )
                
                # Process templates
                processed_files = self.processor.process_templates_batch(
                    template_folder=template_folder,
                    appids=appids,
                    output_folder=self.config.paths.output_processed
                )
                
                self.logger.info(
                    f"Successfully prepared {len(processed_files)} prequal test data files"
                )
                
                return processed_files
                
        except Exception as e:
            if isinstance(e, TestDataPreparationError):
                raise
            raise TestDataPreparationError(
                "Failed to prepare prequal test data",
                data_type="prequal",
                step="preparation",
                original_error=e
            )
    
    def prepare_all_test_data(self) -> List[TestDataFile]:
        """
        Prepare both regular and prequal test data.
        
        Returns:
            List of all processed test data files
            
        Raises:
            TestDataPreparationError: If preparation fails
        """
        try:
            with PerformanceLogger(self.logger, "Prepare All Test Data"):
                all_files = []
                
                # Prepare regular test data
                try:
                    regular_files = self.prepare_regular_test_data()
                    all_files.extend(regular_files)
                except Exception as e:
                    self.logger.error(f"Failed to prepare regular test data: {e}")
                    # Continue to prequal even if regular fails
                
                # Prepare prequal test data
                try:
                    prequal_files = self.prepare_prequal_test_data()
                    all_files.extend(prequal_files)
                except Exception as e:
                    self.logger.error(f"Failed to prepare prequal test data: {e}")
                
                if not all_files:
                    raise TestDataPreparationError(
                        "Failed to prepare any test data",
                        data_type="both",
                        step="preparation"
                    )
                
                self.logger.info(
                    f"Successfully prepared {len(all_files)} total test data files"
                )
                
                return all_files
                
        except Exception as e:
            if isinstance(e, TestDataPreparationError):
                raise
            raise TestDataPreparationError(
                "Failed to prepare all test data",
                data_type="both",
                step="preparation",
                original_error=e
            )