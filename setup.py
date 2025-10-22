from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cortex-sdk",
    version="0.1.0",
    author="Astra Veda Labs",
    author_email="contact@astraveda.ai",
    description="A powerful Python SDK for intelligent memory management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/cortex-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "torch>=1.9.0",
        "transformers>=4.20.0",
        "sentence-transformers>=2.0.0",
        "scikit-learn>=0.24.0",
        "pydantic>=1.9.0",
        "click>=8.0.0",
        "tqdm>=4.60.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "ipython>=8.0.0",
            "jupyter>=1.0.0",
        ],
        "postgres": [
            "psycopg2-binary>=2.9.0",
            "pgvector>=0.1.0",
        ],
        "sqlite": [
            "sqlite-vec>=0.0.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "cortex=cortex.cli.cortex_cli:cli",
        ],
    },
)

