#!/usr/bin/env python3
"""
Test script for Statistical Arbitrage System
Run this to verify all components are working correctly
"""

import sys
import os
import traceback
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test all required imports"""
    print("Testing imports...")

    try:
        import pandas as pd
        import numpy as np
        import yfinance as yf
        import matplotlib.pyplot as plt
        import seaborn as sns
        from scipy import stats
        from statsmodels.tsa.stattools import coint, adfuller
        from sklearn.linear_model import LinearRegression
        print("✓ All required packages imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import error: {str(e)}")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")

    try:
        from config.config import TradingConfig, PairTradingConfig, ZerodhaFeeStructure

        trading_config = TradingConfig()
        pair_config = PairTradingConfig()
        fee_structure = ZerodhaFeeStructure()

        print(f"✓ Trading config loaded: Z-score entry = {trading_config.Z_SCORE_ENTRY}")
        print(f"✓ Pair config loaded: {len(pair_config.DEFAULT_PAIRS)} default pairs")
        print(f"✓ Fee structure loaded: Intraday brokerage = {fee_structure.INTRADAY_BROKERAGE_PERCENT*100}%")
        return True

    except Exception as e:
        print(f"✗ Configuration error: {str(e)}")
        traceback.print_exc()
        return False

def test_fee_calculator():
    """Test fee calculator"""
    print("\nTesting fee calculator...")

    try:
        from src.fee_calculator import ZerodhaFeeCalculator

        calculator = ZerodhaFeeCalculator()

        # Test calculation
        result = calculator.calculate_total_charges(
            quantity=100,
            buy_price=1500.0,
            sell_price=1510.0,
            trade_type="intraday"
        )

        print(f"✓ Fee calculation successful")
        print(f"  - Total charges: ₹{result['totals']['total_charges']}")
        print(f"  - Net profit: ₹{result['totals']['net_profit']}")
        print(f"  - Profit %: {result['totals']['net_profit_percent']}%")

        return True

    except Exception as e:
        print(f"✗ Fee calculator error: {str(e)}")
        traceback.print_exc()
        return False

def test_engine():
    """Test statistical arbitrage engine"""
    print("\nTesting statistical arbitrage engine...")

    try:
        from src.stat_arb_engine import StatisticalArbitrageEngine

        engine = StatisticalArbitrageEngine()

        # Test data fetching (with a small sample)
        print("  Testing data fetch...")
        data = engine.fetch_stock_data('RELIANCE.NS', period='1mo')

        if not data.empty:
            print(f"  ✓ Data fetched: {len(data)} days of RELIANCE.NS data")
        else:
            print("  ⚠ Warning: No data fetched (might be due to market hours/holidays)")

        print("✓ Engine initialized successfully")
        return True

    except Exception as e:
        print(f"✗ Engine error: {str(e)}")
        traceback.print_exc()
        return False

def test_pair_analysis():
    """Test pair analysis functionality"""
    print("\nTesting pair analysis...")

    try:
        from src.stat_arb_engine import StatisticalArbitrageEngine

        engine = StatisticalArbitrageEngine()

        print("  Analyzing sample pair (this may take a moment)...")

        # Test with a smaller time period for faster testing
        result = engine.analyze_pair('RELIANCE.NS', 'ONGC.NS', period='3mo')

        if 'error' not in result:
            print(f"  ✓ Pair analysis completed")
            print(f"    - Pair: {result.get('pair', 'Unknown')}")
            print(f"    - Cointegrated: {result.get('cointegrated', False)}")
            if result.get('cointegrated'):
                print(f"    - P-value: {result['cointegration_details']['p_value']:.4f}")
                print(f"    - Current signal: {result['current_signal']['signal']}")
        else:
            print(f"  ⚠ Warning: Pair analysis returned error: {result['error']}")

        return True

    except Exception as e:
        print(f"✗ Pair analysis error: {str(e)}")
        traceback.print_exc()
        return False

def test_gui_imports():
    """Test GUI-related imports"""
    print("\nTesting GUI imports...")

    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        print("✓ All GUI components imported successfully")
        return True

    except Exception as e:
        print(f"✗ GUI import error: {str(e)}")
        print("  Note: If you're running on a server without display, GUI tests will fail")
        return False

def run_all_tests():
    """Run all tests"""
    print("Statistical Arbitrage System - Component Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_config),
        ("Fee Calculator", test_fee_calculator),
        ("Engine Core", test_engine),
        ("Pair Analysis", test_pair_analysis),
        ("GUI Components", test_gui_imports),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {str(e)}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("-" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:.<30} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run 'python main.py' to launch the dashboard")
        print("2. Click 'Screen Pairs' to find viable trading pairs")
        print("3. Start monitoring for real-time signals")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Check internet connection for data fetching")
        print("3. Ensure Python 3.8+ is being used")

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()

    # Keep console open on Windows
    if sys.platform.startswith('win'):
        input("\nPress Enter to exit...")

    sys.exit(0 if success else 1)
