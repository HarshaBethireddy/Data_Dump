#!/usr/bin/env python3
"""
Main execution script for API Test Framework v2.0

Enterprise-grade test runner with comprehensive CLI interface,
async execution, and beautiful reporting.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from api_test_framework.cli.main import app

if __name__ == "__main__":
    # Run the CLI application
    app()