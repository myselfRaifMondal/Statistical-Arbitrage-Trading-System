"""
Setup script for Statistical Arbitrage Trading System
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="statistical-arbitrage-system",
    version="1.0.0",
    author="Statistical Arbitrage Developer",
    author_email="your.email@example.com",
    description="Advanced statistical arbitrage trading system for Indian stock markets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/statistical-arbitrage-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "yfinance>=0.2.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "scipy>=1.9.0",
        "statsmodels>=0.13.0",
        "scikit-learn>=1.1.0",
        "python-dotenv>=0.19.0",
        "requests>=2.28.0",
        "pytz>=2022.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=0.991",
        ],
    },
    entry_points={
        "console_scripts": [
            "stat-arb=statistical_arbitrage.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "statistical_arbitrage": [
            "config/*.py",
            "data/*.csv",
            "logs/*.log",
        ],
    },
)
