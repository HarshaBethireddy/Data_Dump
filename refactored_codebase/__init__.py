"""
Enterprise-grade API Testing Framework

A comprehensive, modular, and scalable API testing framework following
SOLID principles and modern Python best practices.

Version: 2.0.0
Author: Enterprise Development Team
"""

__version__ = "2.0.0"
__author__ = "Enterprise Development Team"

from .core.framework import APITestFramework
from .core.config import ConfigurationManager
from .core.logger import FrameworkLogger

__all__ = [
    "APITestFramework",
    "ConfigurationManager", 
    "FrameworkLogger"
]