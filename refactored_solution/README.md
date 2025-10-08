# Enhanced API Testing Framework

A comprehensive, refactored API testing framework with improved performance, error handling, and reporting capabilities.

## 🚀 Key Improvements

### ✅ **Fixed Critical Flaws:**
- **Resource Leaks**: Proper file handling with context managers
- **Think Time Logic**: Fixed to apply before requests, not after
- **Code Duplication**: Merged duplicate comparison and test data scripts
- **Missing Configuration**: Robust configuration management system
- **Error Handling**: Comprehensive error handling throughout
- **20-Digit Number Support**: Safe handling of large prequal numbers using Decimal

### 🔧 **Enhanced Features:**
- **Modular Architecture**: Clean separation of concerns
- **Centralized Configuration**: Single configuration management system
- **Advanced Logging**: Structured logging with multiple levels
- **Retry Logic**: Built-in retry mechanism for failed requests
- **Better Reports**: Enhanced HTML reports with statistics and analysis
- **Input Validation**: Comprehensive validation of inputs and paths
- **Performance Optimization**: Improved parallel execution and resource management

## 📁 Project Structure

```
refactored_solution/
├── config/
│   ├── __init__.py
│   └── settings.py              # Centralized configuration management
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Centralized logging system
│   └── run_manager.py          # Run ID and folder management
├── data_processor/
│   ├── __init__.py
│   └── test_data_manager.py    # Unified test data processing
├── api_client/
│   ├── __init__.py
│   └── http_client.py          # Enhanced HTTP client with retry logic
├── reporting/
│   ├── __init__.py
│   ├── report_generator.py     # Enhanced HTML report generation
│   └── csv_merger.py           # Improved CSV merging functionality
├── comparison/
│   ├── __init__.py
│   └── json_comparator.py      # Enhanced JSON comparison
├── batch_scripts/
│   ├── run_tests.bat           # Execute full test cycle
│   ├── compare_results.bat     # Compare test results
│   └── merge_csv.bat           # Merge CSV files
├── main_runner.py              # Main framework orchestrator
├── requirements.txt            # Clean dependency list
└── README.md                   # This file
```

## 🛠️ Setup and Installation

### Prerequisites
- Python 3.7+
- Required folders in parent directory:
  - `FullSetRequest/` (JSON template files)
  - `Prequal Request/` (Prequal JSON template files)
  - `MasterTestdata.xlsx` (Regular test data)
  - `PreQual_MasterTestdata.xlsx` (Prequal test data)
  - `api_config.csv` (API configuration)

### Installation
1. Copy the `refactored_solution` folder to your project directory
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### API Configuration
Create `api_config.csv` in the parent directory:
```csv
API_URL,Host
http://your-api-endpoint.com/api,your-host.com
```

## 🚀 Usage

### Method 1: Using Batch Scripts (Recommended)
```bash
# Run full test cycle
cd refactored_solution
batch_scripts\run_tests.bat

# Compare test results
batch_scripts\compare_results.bat

# Merge CSV files
batch_scripts\merge_csv.bat
```

### Method 2: Using Command Line
```bash
cd refactored_solution

# Run tests with both data types
python main_runner.py test --data-type both

# Run tests with specific data type
python main_runner.py test --data-type regular
python main_runner.py test --data-type prequal

# Compare results
python main_runner.py compare --pre-folder 100001 --post-folder 100002

# Merge CSV files
python main_runner.py merge --csv-folder 100001_vs_100002
```

### Method 3: Programmatic Usage
```python
from refactored_solution.main_runner import APITestFramework

# Initialize framework
framework = APITestFramework()

# Run full test cycle
results = framework.run_full_test_cycle(data_type="both")
print(f"Tests completed: {results['successful_tests']}/{results['test_results']}")
```

## 📊 Features

### 1. **Enhanced Test Data Management**
- Unified processor for both regular and prequal data
- Safe handling of 20-digit numbers using Decimal arithmetic
- Automatic APPID increment and replacement
- Comprehensive input validation

### 2. **Robust API Testing**
- Parallel execution with configurable worker count
- Built-in retry logic with exponential backoff
- Proper session management and connection pooling
- Think time applied correctly (before requests)
- Comprehensive error handling and logging

### 3. **Advanced Reporting**
- Beautiful HTML reports with statistics
- Response time analysis
- Status code distribution
- Error analysis and highlighting
- Progress tracking and execution summaries

### 4. **Intelligent Comparison**
- Deep JSON structure comparison
- Handles empty files and parsing errors
- Generates detailed difference reports
- Summary statistics and analysis

### 5. **Enhanced CSV Merging**
- Groups files by common prefixes
- Professional Excel formatting
- Auto-adjusting column widths
- Multiple encoding support
- Error handling for corrupted files

## 🔧 Configuration Options

### Test Configuration (config/settings.py)
```python
@dataclass
class TestConfig:
    parallel_count: int = 2        # Number of parallel requests
    think_time: float = 3.0        # Delay between requests (seconds)
    max_retries: int = 3           # Maximum retry attempts
    retry_delay: float = 1.0       # Delay between retries (seconds)
```

### API Configuration
```python
@dataclass
class APIConfig:
    url: str                       # API endpoint URL
    host: str                      # Host header value
    timeout: int = 30              # Request timeout (seconds)
    verify_ssl: bool = False       # SSL verification
```

## 📈 Performance Improvements

1. **Memory Management**: Proper file handling with context managers
2. **Connection Pooling**: Reused HTTP sessions for better performance
3. **Parallel Optimization**: Fixed think time logic for true parallelism
4. **Resource Cleanup**: Automatic cleanup of resources and connections
5. **Efficient Data Processing**: Optimized JSON and Excel operations

## 🐛 Error Handling

- **Comprehensive Logging**: All operations logged with appropriate levels
- **Graceful Degradation**: Framework continues operation despite individual failures
- **Detailed Error Messages**: Clear error descriptions with context
- **Input Validation**: Validates all inputs before processing
- **Recovery Mechanisms**: Automatic retry for transient failures

## 📁 Output Structure

```
TestResponse/
├── 100001/                    # Run-specific response folder
│   ├── file1_response.json
│   └── file2_response.json
Report/
├── 100001/                    # Run-specific report folder
│   ├── framework.log
│   └── test_report.html
CompareResult/
├── 100001_vs_100002/         # Comparison results
│   ├── comparison_summary.txt
│   └── file1_comparison_result.csv
MergedOut_File/
└── 2024010115/               # Timestamped merge results
    └── merged_files.xlsx
```

## 🔍 Troubleshooting

### Common Issues:
1. **Missing api_config.csv**: Create the file with proper API_URL and Host values
2. **Permission Errors**: Ensure write permissions for output directories
3. **Import Errors**: Make sure you're running from the correct directory
4. **Large Numbers**: Prequal 20-digit numbers are handled as strings to prevent overflow

### Debug Mode:
Enable detailed logging by modifying the log level in `utils/logger.py`:
```python
self._logger.setLevel(logging.DEBUG)
```

## 🎯 Migration from Original Framework

1. Copy your existing data files (Excel, JSON templates, api_config.csv)
2. Replace batch file calls with new batch scripts
3. Update any custom scripts to use the new main_runner.py interface
4. Review and update configuration in config/settings.py if needed

## 📝 License

This enhanced framework maintains compatibility with your existing workflow while providing significant improvements in reliability, performance, and maintainability.