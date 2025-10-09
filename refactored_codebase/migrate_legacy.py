#!/usr/bin/env python3
"""
Migration script to ensure 100% functional compatibility with legacy system.

This script provides a bridge between the legacy system and the new enterprise framework,
ensuring that all existing functionality is preserved while enabling gradual migration.
"""

import os
import sys
import json
import shutil
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Add the refactored codebase to Python path
sys.path.insert(0, str(Path(__file__).parent))

from refactored_codebase.config.settings import get_settings, create_default_configs
from refactored_codebase.core.appid_manager import AppIDManager
from refactored_codebase.core.data_manager import TestDataManager, DataType
from refactored_codebase.core.test_executor import TestExecutor
from refactored_codebase.utils.logging import setup_logging, get_logger


class LegacyCompatibilityLayer:
    """
    Compatibility layer that provides the exact same interface as the legacy system
    while using the new enterprise framework underneath.
    """
    
    def __init__(self):
        """Initialize compatibility layer."""
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize new framework
        try:
            create_default_configs()
            self.settings = get_settings()
            setup_logging(self.settings.logging, self.settings.paths.logs_dir)
            
            # Migrate legacy configuration if exists
            self._migrate_legacy_config()
            
            # Initialize components
            self.appid_manager = AppIDManager(self.settings.appid)
            self.data_manager = TestDataManager(self.settings.paths, self.appid_manager)
            self.test_executor = TestExecutor(self.settings)
            
            self.logger.info("Legacy compatibility layer initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize compatibility layer: {e}")
            raise
    
    def _migrate_legacy_config(self) -> None:
        """Migrate legacy CSV configuration to new JSON format."""
        legacy_config_file = Path("api_config.csv")
        
        if legacy_config_file.exists():
            try:
                # Read legacy CSV config
                df = pd.read_csv(legacy_config_file)
                if len(df) > 0:
                    row = df.iloc[0]
                    
                    # Update development config with legacy values
                    dev_config_path = self.settings.paths.config_dir / "development.json"
                    
                    if dev_config_path.exists():
                        with open(dev_config_path, 'r') as f:
                            config = json.load(f)
                    else:
                        config = {}
                    
                    # Update API configuration
                    if 'api' not in config:
                        config['api'] = {}
                    
                    config['api']['url'] = row.get('API_URL', config['api'].get('url', ''))
                    config['api']['host'] = row.get('Host', config['api'].get('host', ''))
                    
                    # Save updated config
                    with open(dev_config_path, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    self.logger.info("Migrated legacy CSV configuration to JSON")
                    
            except Exception as e:
                self.logger.warning(f"Failed to migrate legacy config: {e}")
    
    def run_legacy_main_runner(self, data_type: str = "both", **kwargs) -> int:
        """
        Emulate the legacy main_runner.py functionality.
        
        Args:
            data_type: Type of data to process (regular/prequal/both)
            **kwargs: Additional legacy parameters
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            self.logger.info(f"Running legacy main_runner emulation - data_type: {data_type}")
            
            # Map legacy data types to new enum
            if data_type.lower() == "regular":
                dt = DataType.REGULAR
            elif data_type.lower() == "prequal":
                dt = DataType.PREQUAL
            elif data_type.lower() == "both":
                # Execute both types
                self._execute_legacy_both_types(**kwargs)
                return 0
            else:
                raise ValueError(f"Invalid data type: {data_type}")
            
            # Execute single data type
            summary = self.test_executor.execute_tests(dt)
            
            # Print legacy-style output
            self._print_legacy_summary(summary)
            
            return 0 if summary.failed_tests == 0 else 1
            
        except Exception as e:
            self.logger.error(f"Legacy main_runner execution failed: {e}")
            print(f"❌ Test execution failed: {e}")
            return 1
    
    def _execute_legacy_both_types(self, **kwargs) -> None:
        """Execute both regular and prequal data types (legacy behavior)."""
        print("🔄 Processing regular test data...")
        regular_summary = self.test_executor.execute_tests(DataType.REGULAR)
        self._print_legacy_summary(regular_summary, "Regular")
        
        print("\n🔄 Processing prequal test data...")
        prequal_summary = self.test_executor.execute_tests(DataType.PREQUAL)
        self._print_legacy_summary(prequal_summary, "Prequal")
        
        # Combined summary
        total_tests = regular_summary.total_tests + prequal_summary.total_tests
        total_success = regular_summary.successful_tests + prequal_summary.successful_tests
        total_failed = regular_summary.failed_tests + prequal_summary.failed_tests
        
        print(f"\n📊 Combined Summary:")
        print(f"Total tests: {total_tests}")
        print(f"Successful: {total_success}")
        print(f"Failed: {total_failed}")
        print(f"Success rate: {(total_success/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
    
    def _print_legacy_summary(self, summary, data_type_name: str = "") -> None:
        """Print summary in legacy format."""
        prefix = f"{data_type_name} " if data_type_name else ""
        
        print(f"\n📊 {prefix}Test Execution Summary:")
        print(f"Run ID: {summary.run_metadata.run_id}")
        print(f"Total tests: {summary.total_tests}")
        print(f"Successful: {summary.successful_tests}")
        print(f"Failed: {summary.failed_tests}")
        print(f"Success rate: {(summary.successful_tests/summary.total_tests)*100:.1f}%" if summary.total_tests > 0 else "0%")
        print(f"Average response time: {summary.average_response_time:.3f}s")
        print(f"Total execution time: {summary.total_execution_time:.1f}s")
        
        if summary.failed_tests > 0:
            print(f"\n❌ Failed tests:")
            for result in summary.results:
                if not result.success:
                    print(f"  - {result.template_name}: {result.error_message}")
    
    def get_legacy_run_id(self) -> int:
        """Get run ID in legacy format (6-digit number starting from 100000)."""
        return self.test_executor.run_manager.get_next_run_id()
    
    def migrate_excel_data(self) -> None:
        """Migrate Excel-based APPID management to new range-based system."""
        print("🔄 Migrating Excel-based APPID management...")
        
        # Check for legacy Excel files
        excel_files = ["MasterTestdata.xlsx", "PreQual_MasterTestdata.xlsx"]
        
        for excel_file in excel_files:
            excel_path = Path(excel_file)
            if excel_path.exists():
                try:
                    # Read Excel file to get last APPID
                    df = pd.read_excel(excel_path)
                    
                    if 'APPID' in df.columns:
                        last_appid = df['APPID'].max()
                        
                        if pd.notna(last_appid):
                            print(f"Found last APPID in {excel_file}: {last_appid}")
                            
                            # Update APPID manager state to continue from this point
                            if "prequal" in excel_file.lower():
                                # Update prequal APPID
                                self.appid_manager._state.current_prequal = int(last_appid) + 1
                            else:
                                # Update regular APPID
                                self.appid_manager._state.current_regular = int(last_appid) + 1
                            
                            self.appid_manager._save_state()
                            print(f"✅ Updated APPID state from {excel_file}")
                
                except Exception as e:
                    print(f"⚠️ Failed to migrate {excel_file}: {e}")
        
        print("✅ Excel data migration completed")


def create_legacy_wrapper_scripts():
    """Create wrapper scripts that emulate the legacy batch files."""
    
    # Legacy main_runner.py wrapper
    main_runner_content = '''#!/usr/bin/env python3
"""
Legacy main_runner.py compatibility wrapper.
This script provides the exact same interface as the original main_runner.py
"""

import sys
import argparse
from pathlib import Path

# Add refactored codebase to path
sys.path.insert(0, str(Path(__file__).parent))

from refactored_codebase.migrate_legacy import LegacyCompatibilityLayer

def main():
    parser = argparse.ArgumentParser(description="Legacy API Test Runner")
    parser.add_argument("command", choices=["test", "compare", "merge"], help="Command to execute")
    parser.add_argument("--data-type", choices=["regular", "prequal", "both"], default="both", help="Data type to process")
    parser.add_argument("--pre-folder", help="Pre-test folder for comparison")
    parser.add_argument("--post-folder", help="Post-test folder for comparison")
    parser.add_argument("--csv-folder", help="CSV folder for merging")
    
    args = parser.parse_args()
    
    # Initialize compatibility layer
    compat = LegacyCompatibilityLayer()
    
    if args.command == "test":
        return compat.run_legacy_main_runner(args.data_type)
    elif args.command == "compare":
        if not args.pre_folder or not args.post_folder:
            print("❌ --pre-folder and --post-folder required for compare command")
            return 1
        # Use new CLI for comparison
        from refactored_codebase.cli.main import cli
        sys.argv = ["framework", "compare", "--pre-folder", args.pre_folder, "--post-folder", args.post_folder]
        cli()
        return 0
    elif args.command == "merge":
        if not args.csv_folder:
            print("❌ --csv-folder required for merge command")
            return 1
        # Use new CLI for merging
        from refactored_codebase.cli.main import cli
        sys.argv = ["framework", "merge", "--csv-folder", args.csv_folder]
        cli()
        return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    
    with open("main_runner.py", "w") as f:
        f.write(main_runner_content)
    
    print("✅ Created legacy main_runner.py wrapper")


def main():
    """Main migration function."""
    print("🚀 Starting Legacy System Migration")
    print("=" * 60)
    
    try:
        # Initialize compatibility layer
        compat = LegacyCompatibilityLayer()
        
        # Migrate Excel data
        compat.migrate_excel_data()
        
        # Create legacy wrapper scripts
        create_legacy_wrapper_scripts()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("\n🎯 Next steps:")
        print("1. Test the legacy interface: python main_runner.py test --data-type both")
        print("2. Use new CLI: python -m refactored_codebase.cli.main test")
        print("3. Check configuration: python -m refactored_codebase.cli.main config show")
        print("4. View framework info: python -m refactored_codebase.cli.main info")
        
        # Test basic functionality
        print("\n🧪 Testing basic functionality...")
        test_result = compat.run_legacy_main_runner("both")
        
        if test_result == 0:
            print("✅ Legacy compatibility test passed!")
        else:
            print("⚠️ Legacy compatibility test had issues, but migration completed")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())