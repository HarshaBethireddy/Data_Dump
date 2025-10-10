# Models Module - API Test Framework v2.0

## 🏗️ **Models Module Completed**

This module contains all data models for the API Test Framework using **Pydantic v2** with modern Python practices.

### ✅ **What We've Built:**

#### 📋 **Base Models** (`base.py`)
- **BaseModel** - Enhanced base with JSON serialization and validation utilities
- **TimestampedModel** - Automatic timestamp tracking with timezone awareness
- **IdentifiableModel** - UUID-based unique identification
- **AppIDModel** - Specialized handling for regular/prequal application IDs
- **ValidationMixin** - Common validation utilities for all models
- **MetadataModel** - Flexible metadata and tagging support

#### 📨 **Request Models** (`request_models.py`)
- **APIRequest** - Base request structure with correlation IDs
- **FullSetRequest** - Complete full set API request validation
- **PrequalRequest** - Prequal API request with 20-digit ID support
- **RequestHeader** - Common header validation with date/time formats
- **DecisionRequest** - Decision request with comprehensive business logic
- **ApplicationInfo** - Nested application data structures
- **BusinessInfo** - Business information with UBO support
- **ApplicantInfo** - Personal and employment information
- **PersonalInfo** - Address and contact validation
- **EmploymentInfo** - Income and employment validation

#### 📬 **Response Models** (`response_models.py`)
- **APIResponse** - Base response with metrics and error handling
- **FullSetResponse** - Full set specific response handling
- **PrequalResponse** - Prequal specific response with bureau data
- **ResponseHeader** - Response header validation
- **DecisionResponse** - Decision results with credit limits and APR
- **ErrorResponse** - Structured error handling with details
- **ValidationResult** - Response validation results
- **ResponseMetrics** - Performance metrics tracking
- **BatchResponse** - Batch operation results

#### 🧪 **Test Models** (`test_models.py`)
- **TestExecution** - Complete test execution tracking
- **TestResult** - Individual test result with validation
- **TestConfiguration** - Test execution parameters
- **TestMetrics** - Performance and timing metrics
- **TestSuite** - Collection of test executions
- **ComparisonResult** - JSON comparison results with diff analysis
- **ComparisonDifference** - Individual difference tracking
- **ReportData** - Report generation data structures

### ✅ **Key Pydantic v2 Features Used:**

#### 🔧 **Modern Validation**
```python
# field_validator instead of validator
@field_validator('email')
@classmethod
def validate_email(cls, v: str) -> str:
    return cls.validate_email_format(v)

# model_validator instead of root_validator
@model_validator(mode='after')
def validate_consistency(self) -> 'ModelName':
    # validation logic
    return self
```

#### ⚙️ **ConfigDict Instead of Config Class**
```python
model_config = ConfigDict(
    validate_assignment=True,
    use_enum_values=True,
    str_strip_whitespace=True,
    extra='forbid'
)
```

#### 🎯 **Advanced Field Validation**
```python
parallel_count: int = Field(default=2, ge=1, le=50, description="Number of parallel requests")
prequal_start: str = Field(default="10000000000000000000", description="20-digit prequal ID")
```

#### 🔄 **Automatic Type Conversion**
```python
# Handles both int and str for app IDs
app_id: Union[int, str] = Field(..., description="Application ID")

# Automatic 20-digit formatting for prequal IDs
if self.app_id_type == 'prequal':
    self.app_id = f"{self.app_id:020d}"
```

### ✅ **Enterprise Features:**

#### 🆔 **Smart ID Management**
- **UUID-based run IDs** replacing magic numbers
- **20-digit prequal ID** support with proper validation
- **Range-based ID generation** configuration
- **Timestamp-based correlation IDs**

#### 📊 **Comprehensive Metrics**
- **Response time tracking** with min/max/average
- **Success rate calculations** 
- **Error categorization** and counting
- **Performance metrics** for optimization

#### 🔍 **Advanced Validation**
- **Email format validation**
- **Phone number normalization**
- **Date format validation** (DDMMYYYY)
- **Postal code validation**
- **Credit limit and APR validation**

#### 🏷️ **Rich Metadata Support**
- **Tagging system** for categorization
- **Custom metadata** key-value pairs
- **Version tracking** for data structures
- **Correlation ID** support for request tracing

### ✅ **Improvements Over Legacy Code:**

| Legacy Issue | ✅ Pydantic v2 Solution |
|-------------|------------------------|
| ❌ No data validation | ✅ Comprehensive field and model validation |
| ❌ Manual JSON parsing | ✅ Automatic serialization/deserialization |
| ❌ No type safety | ✅ Full type hints with runtime validation |
| ❌ Magic number IDs | ✅ UUID-based identification system |
| ❌ Basic error handling | ✅ Structured error models with details |
| ❌ No metrics tracking | ✅ Built-in performance metrics |
| ❌ Manual 20-digit handling | ✅ Automatic prequal ID formatting |
| ❌ No request correlation | ✅ Correlation ID tracking |

### 🎯 **Usage Examples:**

#### Creating a Full Set Request:
```python
from api_test_framework.models import FullSetRequest

request = FullSetRequest(
    application={
        "HEADER": {
            "service_type": "NewACQApp",
            "submit_date": "10082024",
            "submit_time": "14:30:00"
        },
        "DECISIONRQ": {
            "app_id": 1000001,
            "app_id_type": "regular"
        }
    }
)

# Automatic validation and type conversion
header = request.get_header()
decision = request.get_decision_request()
```

#### Creating a Test Execution:
```python
from api_test_framework.models import TestExecution, TestConfiguration

config = TestConfiguration(
    test_name="Load Test",
    test_type="fullset",
    parallel_count=10,
    max_requests=1000
)

execution = TestExecution(
    execution_name="Load Test Run",
    configuration=config
)

execution.start_execution()
# ... run tests ...
execution.complete_execution()
```

#### Handling Prequal IDs:
```python
from api_test_framework.models import AppIDModel

# Automatic 20-digit formatting
app_id_model = AppIDModel(
    app_id=123456789,
    app_id_type="prequal"
)
# app_id becomes "00000000000123456789"

formatted_id = app_id_model.get_formatted_app_id()
```

---

## 🚀 **Ready for Next Module!**

The Models Module provides a solid foundation with:
- ✅ **Type-safe data structures** for all framework operations
- ✅ **Comprehensive validation** with detailed error messages  
- ✅ **Performance metrics** built into the models
- ✅ **Enterprise-grade features** like correlation IDs and metadata
- ✅ **Backward compatibility** with existing JSON structures

**What should we create next?**

1. **🔧 Services Module** - Business logic services (HTTP client, test data, comparison)
2. **🛠️ Utils Module** - Utility functions (file operations, ID generation, validators)
3. **💻 CLI Module** - Command-line interface with rich formatting

I recommend the **Services Module** next, as it will implement the core business logic using our newly created models.

**Should I proceed with creating the Services Module?**