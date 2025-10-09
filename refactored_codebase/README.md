# Enterprise API Testing Framework 2.0

A modern, scalable, and production-ready API testing framework built with enterprise best practices and SOLID principles.

## 🚀 Key Features

### ✨ **Modern Architecture**
- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Clean Code**: Type hints, comprehensive docstrings, consistent naming
- **Modular Design**: Loosely coupled components with high cohesion
- **Enterprise Structure**: Organized folder hierarchy for scalability

### 🔧 **Advanced Configuration Management**
- **JSON-based Configuration**: Environment-specific configs (dev/test/staging/prod)
- **Pydantic Validation**: Type-safe configuration with automatic validation
- **Environment Variables**: Support for 12-factor app methodology
- **Hot Reloading**: Configuration changes without restart

### 🔢 **Modern APPID Management**
- **Range-based Generation**: No more Excel files, use configurable ranges
- **Thread-safe Operations**: Concurrent APPID generation
- **20-digit Prequal Support**: Safe handling of large numbers with Decimal
- **Persistent State**: Atomic file operations with crash recovery

### 🌐 **Enterprise HTTP Client**
- **Connection Pooling**: Efficient resource utilization
- **Retry Logic**: Exponential backoff with configurable strategies
- **Request Tracing**: Comprehensive logging and monitoring
- **SSL/TLS Support**: Configurable certificate verification

### 📊 **Rich CLI Interface**
- **Modern Commands**: Intuitive command structure with rich help
- **Progress Bars**: Real-time progress tracking with Rich library
- **Colored Output**: Beautiful console output with syntax highlighting
- **Interactive Mode**: Guided configuration and validation

### 📈 **Advanced Reporting**
- **JSON Comparison**: Deep object comparison with detailed diff reports
- **Performance Metrics**: Response time analysis and statistics
- **Export Formats**: Excel, CSV, JSON, HTML reports
- **Dashboard Ready**: Structured data for external dashboards

## 📁 Project Structure

```
refactored_codebase/
├── __init__.py                 # Framework metadata
├── requirements.txt            # Dependencies
├── README.md                  # This file
│
├── config/                    # Configuration management
│   ├── __init__.py
│   ├── models.py             # Pydantic configuration models
│   └── settings.py           # Settings management
│
├── core/                     # Core business logic
│   ├── __init__.py
│   ├── appid_manager.py      # Modern APPID management
│   ├── data_manager.py       # Test data processing
│   ├── http_client.py        # Enterprise HTTP client
│   └── run_manager.py        # Run tracking and management
│
├── utils/                    # Utility modules
│   ├── __init__.py
│   ├── logging.py           # Structured logging system
│   ├── json_utils.py        # JSON comparison and validation
│   └── file_utils.py        # File operations
│
├── cli/                     # Command line interface
│   ├── __init__.py
│   ├── main.py             # Main CLI entry point
│   └── commands/           # Command implementations
│       ├── __init__.py
│       ├── test.py         # Test execution
│       ├── compare.py      # Result comparison
│       ├── merge.py        # CSV merging
│       └── config.py       # Configuration management
│
└── data/                   # Data directories (created automatically)
    ├── requests/           # JSON request templates
    │   ├── fullset/       # Regular request templates
    │   └── prequal/       # Prequal request templates
    ├── testdata/          # Test data files (if needed)
    └── output/            # Generated outputs
        ├── responses/     # API responses
        ├── reports/       # Test reports
        ├── comparisons/   # Comparison results
        ├── merged/        # Merged CSV results
        └── logs/          # Log files
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r refactored_codebase/requirements.txt

# Initialize configuration
python -m refactored_codebase.cli.main config init
```

### 2. Configuration

Edit the configuration files in the `config/` directory:

**config/development.json**:
```json
{
  "environment": "development",
  "debug": true,
  "api": {
    "url": "http://your-api-endpoint.com/api",
    "host": "your-api-host.com",
    "timeout": 30,
    "verify_ssl": false
  },
  "appid": {
    "start_range": 100000000,
    "end_range": 999999999,
    "prequal_start_range": 10000000000000000000,
    "prequal_end_range": 99999999999999999999
  }
}
```

### 3. Prepare Test Data

Place your JSON request templates in:
- `data/requests/fullset/` - Regular request templates
- `data/requests/prequal/` - Prequal request templates

Templates should contain `$APPID` placeholder:
```json
{
  "APPLICATION": {
    "DECISIONRQ": {
      "APPID": "$APPID",
      "REQUESTTYPE": "NewApp"
    }
  }
}
```

### 4. Run Tests

```bash
# Run all tests
python -m refactored_codebase.cli.main test

# Run specific data type
python -m refactored_codebase.cli.main test --data-type regular

# Run with custom settings
python -m refactored_codebase.cli.main test --data-type both --parallel 5 --think-time 2.0

# Dry run to validate configuration
python -m refactored_codebase.cli.main test --dry-run
```

## 📋 Available Commands

### Test Execution
```bash
# Execute API tests
python -m refactored_codebase.cli.main test [OPTIONS]

Options:
  --data-type [regular|prequal|both]  Type of test data to process
  --count INTEGER                     Number of requests to process
  --parallel INTEGER                  Number of parallel threads
  --think-time FLOAT                  Think time between requests (seconds)
  --output-dir PATH                   Output directory for results
  --dry-run                          Validate configuration without running tests
```

### Result Comparison
```bash
# Compare two sets of test results
python -m refactored_codebase.cli.main compare [OPTIONS]

Options:
  --pre-folder TEXT                   Pre-test results folder [required]
  --post-folder TEXT                  Post-test results folder [required]
  --output-dir PATH                   Output directory for comparison results
  --ignore-order                     Ignore array order in comparisons
  --ignore-keys TEXT                  Comma-separated list of keys to ignore
```

### CSV Merging
```bash
# Merge CSV files into Excel reports
python -m refactored_codebase.cli.main merge [OPTIONS]

Options:
  --csv-folder TEXT                   Folder containing CSV files to merge [required]
  --output-file TEXT                  Output Excel file name
  --include-summary                   Include summary sheet
```

### Configuration Management
```bash
# Initialize configuration files
python -m refactored_codebase.cli.main config init [--force]

# Show current configuration
python -m refactored_codebase.cli.main config show [--section SECTION]

# Validate configuration
python -m refactored_codebase.cli.main config validate
```

### Framework Information
```bash
# Show framework information and status
python -m refactored_codebase.cli.main info
```

## 🔧 Configuration Reference

### API Configuration
```json
{
  "api": {
    "url": "http://api.example.com",
    "host": "api.example.com",
    "timeout": 30,
    "verify_ssl": false,
    "max_retries": 3,
    "retry_delay": 1.0
  }
}
```

### Test Configuration
```json
{
  "test": {
    "parallel_count": 2,
    "think_time": 3.0,
    "batch_size": 100,
    "enable_comparison": true
  }
}
```

### APPID Configuration
```json
{
  "appid": {
    "start_range": 100000000,
    "end_range": 999999999,
    "prequal_start_range": 10000000000000000000,
    "prequal_end_range": 99999999999999999999,
    "increment": 1
  }
}
```

### Logging Configuration
```json
{
  "logging": {
    "level": "INFO",
    "file_rotation": true,
    "max_file_size": "10MB",
    "backup_count": 5
  }
}
```

## 🏗️ Architecture Principles

### SOLID Principles Implementation

1. **Single Responsibility Principle (SRP)**
   - Each class has one reason to change
   - `AppIDManager` only manages APPID generation
   - `HTTPClient` only handles HTTP communication
   - `TestDataManager` only processes test data

2. **Open/Closed Principle (OCP)**
   - Framework is open for extension, closed for modification
   - New data types can be added without changing existing code
   - Plugin architecture for custom processors

3. **Liskov Substitution Principle (LSP)**
   - Interfaces can be substituted without breaking functionality
   - Abstract base classes define contracts

4. **Interface Segregation Principle (ISP)**
   - Clients depend only on interfaces they use
   - Focused, minimal interfaces

5. **Dependency Inversion Principle (DIP)**
   - High-level modules don't depend on low-level modules
   - Both depend on abstractions
   - Dependency injection throughout

### Clean Code Practices

- **Type Hints**: All functions and methods have type annotations
- **Docstrings**: Comprehensive documentation for all public APIs
- **Error Handling**: Specific exceptions with meaningful messages
- **Logging**: Structured logging with context and tracing
- **Testing**: Unit tests with high coverage (when implemented)

## 🔄 Migration from Legacy System

### Automatic Migration

The framework includes a migration script to help transition from the legacy system:

```bash
python -m refactored_codebase.migrate_data
```

This will:
1. Create the new directory structure
2. Migrate JSON request templates
3. Convert CSV configuration to JSON
4. Preserve existing test data

### Manual Migration Steps

1. **Configuration**: Convert `api_config.csv` to JSON format
2. **Templates**: Move JSON files to new directory structure
3. **APPID Management**: Replace Excel-based system with range configuration
4. **Scripts**: Update batch files to use new CLI commands

## 🚀 Production Deployment

### Environment Configuration

Create environment-specific configuration files:

**config/production.json**:
```json
{
  "environment": "production",
  "debug": false,
  "api": {
    "verify_ssl": true,
    "timeout": 60
  },
  "test": {
    "parallel_count": 10,
    "batch_size": 500
  },
  "logging": {
    "level": "INFO",
    "file_rotation": true
  }
}
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY refactored_codebase/ ./refactored_codebase/
COPY requirements.txt .

RUN pip install -r requirements.txt

ENV ENVIRONMENT=production
CMD ["python", "-m", "refactored_codebase.cli.main", "test", "--data-type", "both"]
```

### CI/CD Integration

```yaml
# .github/workflows/api-tests.yml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r refactored_codebase/requirements.txt
      - run: python -m refactored_codebase.cli.main config validate
      - run: python -m refactored_codebase.cli.main test --dry-run
```

## 📊 Monitoring and Observability

### Structured Logging

The framework provides structured logging with:
- Request/response tracing
- Performance metrics
- Error tracking
- JSON log format for external systems

### Metrics Collection

Key metrics automatically collected:
- Request success/failure rates
- Response times (min/max/avg/p95)
- APPID generation statistics
- Resource utilization

### Integration with External Systems

- **Prometheus**: Metrics export for monitoring
- **ELK Stack**: Log aggregation and analysis
- **Grafana**: Dashboard visualization
- **Alerting**: Automated failure notifications

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd enterprise-api-testing-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r refactored_codebase/requirements.txt
pip install pytest pytest-cov black flake8 mypy

# Run tests
pytest refactored_codebase/tests/

# Code formatting
black refactored_codebase/
flake8 refactored_codebase/
mypy refactored_codebase/
```

### Code Standards

- **Python 3.11+**: Modern Python features
- **Type Hints**: All public APIs must have type annotations
- **Docstrings**: Google-style docstrings for all modules, classes, and functions
- **Testing**: Minimum 80% code coverage
- **Linting**: Pass flake8 and mypy checks
- **Formatting**: Use Black for code formatting

## 📞 Support

### Documentation
- **API Reference**: Auto-generated from docstrings
- **User Guide**: Comprehensive usage examples
- **Architecture Guide**: Design decisions and patterns

### Troubleshooting

Common issues and solutions:

1. **Configuration Errors**: Run `config validate` to check settings
2. **APPID Exhaustion**: Increase range or reset counters
3. **Connection Issues**: Check API endpoint and network connectivity
4. **Performance Issues**: Adjust parallel count and think time

### Getting Help

- **Issues**: Report bugs and feature requests
- **Discussions**: Community support and questions
- **Documentation**: Comprehensive guides and examples

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Enterprise API Testing Framework 2.0** - Built with ❤️ for enterprise-grade API testing.