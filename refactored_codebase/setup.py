"""
Setup script for the Enterprise API Testing Framework.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="enterprise-api-testing-framework",
    version="2.0.0",
    description="Enterprise-grade API testing framework with parallel execution and comprehensive reporting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Enterprise Development Team",
    author_email="dev-team@company.com",
    url="https://github.com/company/api-testing-framework",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.0.280",
            "mypy>=1.5.0",
        ],
        "enhanced": [
            "ujson>=5.8.0",
            "loguru>=0.7.0",
            "pydantic>=2.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "api-test=refactored_codebase.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    keywords="api testing framework enterprise parallel automation",
    project_urls={
        "Bug Reports": "https://github.com/company/api-testing-framework/issues",
        "Source": "https://github.com/company/api-testing-framework",
        "Documentation": "https://api-testing-framework.readthedocs.io/",
    },
)