# Enterprise API Testing Framework 2.0

A comprehensive, enterprise-grade API testing framework built with modern Python practices, following SOLID principles and designed for scalability, maintainability, and reliability.

## 🚀 Key Features

### ✅ **Enterprise Architecture**
- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Clean Code**: DRY, KISS, and comprehensive documentation
- **Modular Design**: Loosely coupled components with dependency injection
- **Type Safety**: Full type hints and validation throughout

### 🔧 **Advanced Capabilities**
- **Multi-Environment Support**: Development, testing, staging, production configurations
- **Parallel Execution**: Configurable concurrent API testing
- **Retry Logic**: Built-in retry mechanisms with exponential backoff
- **Connection Pooling**: Efficient HTTP connection management
- **Comprehensive Logging**: Structured logging with multiple levels and handlers

### 📊 **Rich Reporting**
- **HTML Reports**: Interactive reports with charts and statistics
- **Comparison Analysis**: Detailed diff analysis between test runs
- **Excel Integration**: Automated Excel report generation with formatting
- **CSV Merging**: Combine multiple comparison results

### 🛡️ **Robust Error Handling**
- **Graceful Degradation**: Continues operation despite individual failures
- **Resource Management**: Proper cleanup and resource management
- **Validation**: Configuration and input validation throughout

## 📁 Project Structure

```
refactored_codebase/
├── __init__.py                 # Package initialization
├── core/                       # Core framework components
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging system
│   └── framework.py           # Main framework orchestrator
├── services/                   # Business logic services
│   ├── __init__.py
│   ├── run_manager.py         # Run ID and folder management
│   ├── test_data_service.py   # Test data preparation
│   ├── http_service.py        # HTTP client and parallel execution
│   ├── report_service.py      # Report generation
│   └── comparison_service.py  # Result comparison and merging
├── cli/                       # Command line interface
│   ├── __init__.py
│   └── main.py               # CLI implementation
├── config/                    # Configuration files
│   ├── development.json
│   ├── testing.json
│   └── production.json
├── data/                      # Data directories (created at runtime)
│   ├── requests/
│   │   ├── fullset/
│   │   └── prequal/
│   └── testdata/
├── output/                    # Output directories (created at runtime)
│   ├── json/
│   ├── responses/
│   ├── reports/
│   ├── comparisons/
│   └── merged/
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Installation

1. **Clone or copy the refactored codebase**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup your data structure:**
   ```
   data/
   ├── requests/
   │   ├── fullset/          # Place your fullset JSON templates here
   │   └── prequal/          # Place your prequal JSON templates here
   └── testdata/
       ├── MasterTestdata.xlsx
       └── PreQual_MasterTestdata.xlsx
   ```

4. **Configure your API settings:**
   - Edit `config/development.json` with your API details
   - Or create environment-specific configs

### Basic Usage

```python
# Python API
from refactored_codebase import APITestFramework

# Create and run framework
framework = APITestFramework()
result = framework.run_full_test_cycle(data_type="both")

print(f"Tests completed: {result.successful_tests}/{result.test_results}")
```

```bash
# Command Line Interface
python -m refactored_codebase.cli.main test --data-type both
python -m refactored_codebase.cli.main compare --pre-folder 100001 --post-folder 100002
python -m refactored_codebase.cli.main merge --csv-folder comparison_results
```

## 📖 Detailed Usage

### Configuration Management

The framework supports multiple configuration sources:

1. **JSON Configuration Files** (recommended):
   ```json
   {
     "url": "https://api.example.com/test",
     "host": "api.example.com",
     "timeout": 30,
     "verify_ssl": false
   }
   ```

2. **Environment Variables**:
   ```bash
   export API_URL="https://api.example.com/test"
   export API_HOST="api.example.com"
   export API_TIMEOUT="30"
   ```

3. **CSV Configuration** (legacy support):
   ```csv
   API_URL,Host,timeout,verify_ssl
   https://api.example.com/test,api.example.com,30,false
   ```

### Test Data Preparation

The framework processes JSON templates with Excel data:

1. **Place JSON templates** in `data/requests/fullset/` or `data/requests/prequal/`
2. **Use placeholders** like `$APPID` in your JSON templates
3. **Provide Excel data** with matching column headers
4. **Run the framework** - it automatically substitutes placeholders

### Parallel Execution

Configure parallel execution in your test configuration:

```python
from refactored_codebase.core.config import ConfigurationManager

config = ConfigurationManager()
config.test_config.parallel_count = 5  # 5 concurrent requests
config.test_config.think_time = 2.0    # 2 seconds between requests
```

### Advanced Features

#### Custom Configuration
```python
from refactored_codebase import APITestFramework, ConfigurationManager

# Custom configuration
config = ConfigurationManager(
    config_file="my_config.json",
    environment="production"
)

framework = APITestFramework(config_manager=config)
```

#### Programmatic Usage
```python
# Step-by-step execution
framework = APITestFramework()
framework.initialize()

# Prepare test data
files = framework.prepare_test_data("regular")

# Execute tests
results = framework.execute_api_tests()

# Generate report
report = framework.generate_report(results)
```

#### Result Comparison
```python
# Compare two test runs
comparison = framework.compare_test_results("100001", "100002")
print(f"Files with differences: {comparison['files_with_differences']}")
```

## 🔧 Configuration Options

### API Configuration
- `url`: API endpoint URL
- `host`: Host header value
- `timeout`: Request timeout in seconds
- `verify_ssl`: SSL certificate verification
- `max_retries`: Maximum retry attempts
- `retry_delay`: Delay between retries

### Test Configuration
- `parallel_count`: Number of concurrent requests
- `think_time`: Delay between requests
- `max_retries`: Test-specific retry count
- `retry_delay`: Test-specific retry delay

### Path Configuration
All paths are configurable and use Path objects for cross-platform compatibility.

## 📊 Reports and Analysis

### HTML Reports
- Interactive charts and statistics
- Detailed test results with filtering
- Response time analysis
- Error distribution
- Mobile-responsive design

### Comparison Reports
- Side-by-side result comparison
- Detailed difference analysis
- CSV export for further analysis
- Excel reports with formatting

### Excel Integration
- Automated workbook generation
- Multiple sheets (summary + details)
- Conditional formatting
- Charts and statistics

## 🛠️ Development and Testing

### Code Quality Tools
```bash
# Install development dependencies
pip install black ruff mypy pytest pytest-cov

# Format code
black refactored_codebase/

# Lint code
ruff refactored_codebase/

# Type checking
mypy refactored_codebase/

# Run tests
pytest tests/ --cov=refactored_codebase
```

### Extending the Framework

The framework is designed for extensibility:

1. **Add new data processors** by extending `TestDataProcessor`
2. **Create custom report generators** by extending `ReportGenerator`
3. **Implement new configuration loaders** by implementing `ConfigurationLoader`
4. **Add new CLI commands** by extending the CLI parser

## 🔍 Troubleshooting

### Common Issues

1. **Configuration not found**:
   - Ensure config files exist in the `config/` directory
   - Check file permissions and format

2. **Import errors**:
   - Verify you're running from the correct directory
   - Check Python path and package installation

3. **Test data issues**:
   - Verify Excel files exist and have correct headers
   - Check JSON template syntax and placeholders

4. **Network issues**:
   - Verify API endpoint accessibility
   - Check SSL/TLS configuration
   - Review timeout settings

### Logging

Enable debug logging for detailed troubleshooting:

```bash
python -m refactored_codebase.cli.main test --log-level DEBUG
```

## 🎯 Migration from Original Framework

The refactored framework maintains compatibility while providing significant improvements:

### What's Changed
- **Modular architecture** replaces monolithic design
- **Type safety** throughout the codebase
- **Configuration management** replaces hardcoded values
- **Dependency injection** replaces global state
- **Enterprise patterns** replace ad-hoc implementations

### What's Compatible
- **Excel data format** remains the same
- **JSON templates** work without changes
- **Output structure** is similar but better organized
- **Command-line interface** provides same functionality

## 📝 License

This enterprise framework maintains compatibility with your existing workflow while providing significant improvements in reliability, performance, and maintainability.

## 🤝 Contributing

1. Follow the established architecture patterns
2. Maintain type hints and documentation
3. Add tests for new functionality
4. Follow the code style guidelines
5. Update documentation as needed

---

**Built with ❤️ using modern Python practices and enterprise design patterns.**