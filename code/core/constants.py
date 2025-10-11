from enum import Enum
from typing import Final


class TestDataType(str, Enum):

    FULLSET = "fullset"
    PREQUAL = "prequal"
    BOTH = "both"


class HTTPStatusCategory(str, Enum):

    SUCCESS = "2xx"
    REDIRECTION = "3xx"
    CLIENT_ERROR = "4xx"
    SERVER_ERROR = "5xx"


class FileExtension(str, Enum):

    JSON = ".json"
    CSV = ".csv"
    XLSX = ".xlsx"
    HTML = ".html"
    TXT = ".txt"
    LOG = ".log"


class LogLevel(str, Enum):

    DEBUG = "DEBUG" 
    INFO = "INFO" 
    WARNING = "WARNING" 
    ERROR = "ERROR" 
    CRITICAL = "CRITICAL"


TIMESTAMP_FORMAT: Final[str] = "%Y%m%d_%H%M%S"
RESPONSE_FILE_SUFFIX: Final[str] = "_response"
COMPARISON_FILE_SUFFIX: Final[str] = "_comparison_result"
SUMMARY_FILE_NAME: Final[str] = "summary"

APPID_PLACEHOLDER: Final[str] = "$APPID"

DEFAULT_TIMEOUT: Final[int] = 30