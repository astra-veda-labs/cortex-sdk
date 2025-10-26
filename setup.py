"""
Cortex SDK Setup Script

This script handles the packaging and distribution of the Cortex SDK.
"""

from setuptools import setup, find_packages
import os
import sys

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Get version
def get_version():
    with open("cortex/__init__.py", "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="cortex-sdk",
    version=get_version(),
    author="Cortex SDK Team",
    author_email="cortex@example.com",
    description="Intelligent Memory Management SDK for AI Applications",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/cortex-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "chroma": ["chromadb>=0.4.0"],
        "qdrant": ["qdrant-client>=1.0.0"],
        "lance": ["lance>=0.1.0"],
        "weaviate": ["weaviate-client>=3.0.0"],
        "all": [
            "chromadb>=0.4.0",
            "qdrant-client>=1.0.0", 
            "lance>=0.1.0",
            "weaviate-client>=3.0.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "cortex-cli=cortex_cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "cortex": ["config/*.json", "backends/*.py"],
    },
    exclude_package_data={
        "": ["Chat_bot/*", "docs/*", "tests/*"],
    },
    zip_safe=False,
    keywords="ai, memory, vector, database, semantic, search, cortex, sdk",
    project_urls={
        "Bug Reports": "https://github.com/your-org/cortex-sdk/issues",
        "Source": "https://github.com/your-org/cortex-sdk",
        "Documentation": "https://cortex-sdk.readthedocs.io/",
    },
)