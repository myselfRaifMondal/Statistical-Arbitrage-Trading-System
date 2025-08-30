# Configuration file for Statistical Arbitrage Bot
# Zerodha fee structure and trading parameters

class ZerodhaFeeStructure:
    """
    Zerodha fee structure as per 2025 rates
    All charges are in percentage unless specified
    """

    # Brokerage charges
    DELIVERY_BROKERAGE = 0.0  # Free for delivery
    INTRADAY_BROKERAGE_PERCENT = 0.0003  # 0.03%
    INTRADAY_BROKERAGE_MAX = 20.0  # Max Rs 20 per order

    # STT (Securities Transaction Tax) rates
    STT_DELIVERY_BUY = 0.001  # 0.1% on buy side
    STT_DELIVERY_SELL = 0.001  # 0.1% on sell side
    STT_INTRADAY_SELL = 0.00025  # 0.025% on sell side only

    # Exchange transaction charges (per crore)
    NSE_TRANSACTION_CHARGES = 297.0 / 10000000  # Rs 297 per crore
    BSE_TRANSACTION_CHARGES = 375.0 / 10000000  # Rs 375 per crore

    # SEBI charges
    SEBI_CHARGES = 10.0 / 10000000  # Rs 10 per crore

    # Stamp duty (per crore, on buy side only)
    STAMP_DUTY_DELIVERY = 1500.0 / 10000000  # Rs 1500 per crore
    STAMP_DUTY_INTRADAY = 300.0 / 10000000   # Rs 300 per crore

    # GST on brokerage and transaction charges
    GST_RATE = 0.18  # 18%

    # DP charges (when selling from demat)
    DP_CHARGES = 13.5  # Rs 13.5 per scrip

class TradingConfig:
    """Trading strategy configuration"""

    # Risk management
    MAX_POSITION_SIZE = 0.02  # 2% of portfolio per position
    STOP_LOSS_MULTIPLIER = 2.5  # Stop loss at 2.5 standard deviations
    TAKE_PROFIT_MULTIPLIER = 1.0  # Take profit at 1 standard deviation

    # Entry/Exit thresholds for z-score
    Z_SCORE_ENTRY = 2.0
    Z_SCORE_EXIT = 0.5

    # Lookback periods
    LOOKBACK_PERIOD = 60  # Days for cointegration test
    ROLLING_WINDOW = 20   # Days for rolling statistics

    # Minimum profit threshold (after all costs)
    MIN_PROFIT_THRESHOLD = 0.001  # 0.1% minimum profit required

    # Data refresh intervals
    DATA_REFRESH_MINUTES = 5
    PRICE_UPDATE_SECONDS = 30

class PairTradingConfig:
    """Pairs trading specific configuration"""

    # Stock pairs for analysis
    DEFAULT_PAIRS = [
        ('RELIANCE.NS', 'ONGC.NS'),
        ('HDFCBANK.NS', 'KOTAKBANK.NS'),
        ('TCS.NS', 'INFY.NS'),
        ('ICICIBANK.NS', 'SBIN.NS'),
        ('HINDUNILVR.NS', 'ITC.NS'),
        ('BAJFINANCE.NS', 'HDFCLIFE.NS'),
        ('MARUTI.NS', 'M&M.NS'),
        ('ASIANPAINT.NS', 'BERGER.NS')
    ]

    # Correlation threshold
    MIN_CORRELATION = 0.7

    # Cointegration p-value threshold
    MAX_COINTEGRATION_PVALUE = 0.05

    # Portfolio allocation
    MAX_PAIRS_ACTIVE = 3
    CAPITAL_PER_PAIR = 100000  # Rs 1 lakh per pair

# API Configuration (for future Kite integration)
class APIConfig:
    """API configuration for Kite Connect (future use)"""

    # Kite Connect settings (to be filled when switching from yfinance)
    API_KEY = ""
    API_SECRET = ""
    REQUEST_TOKEN = ""

    # Rate limiting
    MAX_REQUESTS_PER_SECOND = 3
    MAX_ORDERS_PER_SECOND = 10

# Logging configuration
class LoggingConfig:
    """Logging configuration"""

    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "logs/stat_arb.log"
    MAX_LOG_SIZE_MB = 100
    BACKUP_COUNT = 5

# Database configuration (if needed)
class DatabaseConfig:
    """Database configuration for storing trade data"""

    DB_PATH = "data/trades.db"
    BACKUP_INTERVAL_HOURS = 24
