@echo off
echo Statistical Arbitrage Trading System
echo =====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Checking Python version...
python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"

REM Check if requirements are installed
echo.
echo Checking dependencies...
python -c "import pandas, numpy, yfinance, matplotlib, seaborn, scipy, statsmodels, sklearn" 2>nul
if %errorlevel% neq 0 (
    echo Some dependencies are missing. Installing...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo All dependencies are installed
)

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "data" mkdir data

echo.
echo Launching Statistical Arbitrage Dashboard...
echo.
python main.py

if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to start the application
    echo Check the error messages above for details
    pause
)
