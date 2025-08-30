#!/usr/bin/env python3
"""
Statistical Arbitrage Trading System
Main application entry point
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'pandas', 'numpy', 'yfinance', 'matplotlib', 
        'seaborn', 'scipy', 'statsmodels', 'sklearn'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        error_msg = f"""
Missing required packages: {', '.join(missing_packages)}

Please install them using:
pip install {' '.join(missing_packages)}

Or install all requirements:
pip install -r requirements.txt
"""
        print(error_msg)
        return False

    return True

def setup_directories():
    """Setup required directories"""
    directories = ['logs', 'data']

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def setup_logging():
    """Setup application logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('logs/stat_arb.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger('StatArb')
    logger.info("Statistical Arbitrage System Starting...")
    return logger

def main():
    """Main application entry point"""
    print("Statistical Arbitrage Trading System")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        sys.exit(1)

    # Setup directories and logging
    setup_directories()
    logger = setup_logging()

    try:
        # Import dashboard after dependency check
        from dashboard import StatisticalArbitrageDashboard

        # Create main window
        root = tk.Tk()

        # Handle window close event
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
                logger.info("Application shutdown by user")
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Configure window
        root.title("Statistical Arbitrage Trading System")
        root.geometry("1400x900")

        # Set window icon (if available)
        try:
            # You can add an icon file later
            pass
        except:
            pass

        # Create application
        app = StatisticalArbitrageDashboard(root)
        logger.info("Dashboard initialized successfully")

        # Center window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

        print("\nDashboard launched successfully!")
        print("Check the logs/stat_arb.log file for detailed logging.")

        # Start the GUI
        root.mainloop()

    except ImportError as e:
        error_msg = f"Failed to import required modules: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        input("Press Enter to exit...")
        sys.exit(1)

    except Exception as e:
        error_msg = f"Failed to start application: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        messagebox.showerror("Error", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
