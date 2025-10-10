"""
Setup script for API Test Framework v2.0
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="api-test-framework",
    version="2.0.0",
    description="Enterprise-grade API testing framework with advanced reporting and comparison capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="API Test Framework Team",
    author_email="team@example.com",
    url="https://github.com/your-org/api-test-framework",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "api-test=api_test_framework.cli.main:app",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    keywords=["api", "testing", "automation", "framework", "comparison"],
    include_package_data=True,
    package_data={
        "api_test_framework": [
            "templates/*.html",
            "config/*.json",
            "data/**/*.json",
        ],
    },
)