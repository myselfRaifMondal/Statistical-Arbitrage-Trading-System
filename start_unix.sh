#!/bin/bash

echo "Statistical Arbitrage Trading System"
echo "====================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Error: Python is not installed"
        echo "Please install Python 3.8+ from your package manager or python.org"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Checking Python version..."
$PYTHON_CMD -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    if ! command -v pip &> /dev/null; then
        echo "Error: pip is not installed"
        echo "Please install pip for your Python installation"
        exit 1
    else
        PIP_CMD="pip"
    fi
else
    PIP_CMD="pip3"
fi

# Check if requirements are installed
echo
echo "Checking dependencies..."
$PYTHON_CMD -c "import pandas, numpy, yfinance, matplotlib, seaborn, scipy, statsmodels, sklearn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Some dependencies are missing. Installing..."
    $PIP_CMD install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        echo "You might need to run: sudo $PIP_CMD install -r requirements.txt"
        exit 1
    fi
else
    echo "All dependencies are installed"
fi

# Create necessary directories
mkdir -p logs
mkdir -p data

echo
echo "Launching Statistical Arbitrage Dashboard..."
echo
$PYTHON_CMD main.py

if [ $? -ne 0 ]; then
    echo
    echo "Error: Failed to start the application"
    echo "Check the error messages above for details"
    read -p "Press Enter to exit..."
fi
