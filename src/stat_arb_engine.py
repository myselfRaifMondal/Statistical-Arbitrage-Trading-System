"""
Statistical Arbitrage Engine
Handles pair identification, cointegration testing, and trading signals
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats
from statsmodels.tsa.stattools import coint, adfuller
from sklearn.linear_model import LinearRegression
import warnings
import logging
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.config import TradingConfig, PairTradingConfig
from src.fee_calculator import ZerodhaFeeCalculator

warnings.filterwarnings('ignore')

class StatisticalArbitrageEngine:
    """Main engine for statistical arbitrage trading"""

    def __init__(self):
        self.trading_config = TradingConfig()
        self.pair_config = PairTradingConfig()
        self.fee_calculator = ZerodhaFeeCalculator()
        self.logger = self._setup_logger()
        self.pairs_data = {}
        self.active_signals = {}

    def _setup_logger(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('../logs/stat_arb.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('StatArb')

    def fetch_stock_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """
        Fetch stock data from Yahoo Finance

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            period: Data period ('1y', '6mo', '3mo', etc.)

        Returns:
            DataFrame with stock data
        """
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period)

            if data.empty:
                self.logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            # Clean the data
            data = data.dropna()
            data['Symbol'] = symbol

            self.logger.info(f"Fetched {len(data)} days of data for {symbol}")
            return data

        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def test_cointegration(self, price_series_1: pd.Series, price_series_2: pd.Series) -> dict:
        """
        Test for cointegration between two price series

        Args:
            price_series_1: First stock price series
            price_series_2: Second stock price series

        Returns:
            Dictionary with cointegration test results
        """
        try:
            # Align the series by index
            aligned_data = pd.DataFrame({
                'stock1': price_series_1,
                'stock2': price_series_2
            }).dropna()

            if len(aligned_data) < 30:  # Need sufficient data
                return {
                    'cointegrated': False,
                    'p_value': 1.0,
                    'critical_value': None,
                    'hedge_ratio': None,
                    'error': 'Insufficient data'
                }

            # Perform Engle-Granger cointegration test
            coint_result = coint(aligned_data['stock1'], aligned_data['stock2'])
            p_value = coint_result[1]
            critical_value = coint_result[2][1]  # 5% critical value

            # Calculate hedge ratio using linear regression
            lr = LinearRegression()
            X = aligned_data['stock1'].values.reshape(-1, 1)
            y = aligned_data['stock2'].values
            lr.fit(X, y)
            hedge_ratio = lr.coef_[0]

            is_cointegrated = p_value < self.pair_config.MAX_COINTEGRATION_PVALUE

            return {
                'cointegrated': is_cointegrated,
                'p_value': p_value,
                'critical_value': critical_value,
                'hedge_ratio': hedge_ratio,
                'intercept': lr.intercept_,
                'r_squared': lr.score(X, y),
                'data_points': len(aligned_data)
            }

        except Exception as e:
            self.logger.error(f"Error in cointegration test: {str(e)}")
            return {
                'cointegrated': False,
                'p_value': 1.0,
                'error': str(e)
            }

    def calculate_spread(self, price_series_1: pd.Series, price_series_2: pd.Series, 
                        hedge_ratio: float, intercept: float = 0) -> pd.Series:
        """
        Calculate the spread between two cointegrated series

        Args:
            price_series_1: First stock price series
            price_series_2: Second stock price series
            hedge_ratio: Hedge ratio from cointegration test
            intercept: Intercept from linear regression

        Returns:
            Spread series
        """
        try:
            # Align the series
            aligned_data = pd.DataFrame({
                'stock1': price_series_1,
                'stock2': price_series_2
            }).dropna()

            # Calculate spread: stock2 - hedge_ratio * stock1 - intercept
            spread = aligned_data['stock2'] - (hedge_ratio * aligned_data['stock1'] + intercept)

            return spread

        except Exception as e:
            self.logger.error(f"Error calculating spread: {str(e)}")
            return pd.Series()

    def calculate_zscore(self, spread: pd.Series, window: int = None) -> pd.Series:
        """
        Calculate z-score of the spread for trading signals

        Args:
            spread: Spread series
            window: Rolling window for z-score calculation

        Returns:
            Z-score series
        """
        if window is None:
            window = self.trading_config.ROLLING_WINDOW

        try:
            # Calculate rolling mean and standard deviation
            rolling_mean = spread.rolling(window=window, min_periods=window//2).mean()
            rolling_std = spread.rolling(window=window, min_periods=window//2).std()

            # Calculate z-score
            z_score = (spread - rolling_mean) / rolling_std

            return z_score

        except Exception as e:
            self.logger.error(f"Error calculating z-score: {str(e)}")
            return pd.Series()

    def generate_trading_signals(self, z_score: pd.Series, spread: pd.Series) -> pd.DataFrame:
        """
        Generate trading signals based on z-score

        Args:
            z_score: Z-score series
            spread: Original spread series

        Returns:
            DataFrame with trading signals
        """
        try:
            signals = pd.DataFrame(index=z_score.index)
            signals['z_score'] = z_score
            signals['spread'] = spread
            signals['signal'] = 0  # 0: no position, 1: long pair, -1: short pair
            signals['position'] = 0  # Track current position

            current_position = 0

            for i in range(1, len(signals)):
                z_current = signals.iloc[i]['z_score']

                if pd.isna(z_current):
                    signals.iloc[i, signals.columns.get_loc('signal')] = 0
                    signals.iloc[i, signals.columns.get_loc('position')] = current_position
                    continue

                # Entry signals
                if current_position == 0:  # No position
                    if z_current > self.trading_config.Z_SCORE_ENTRY:
                        # Spread too high, short the pair (short stock2, long stock1)
                        signals.iloc[i, signals.columns.get_loc('signal')] = -1
                        current_position = -1
                    elif z_current < -self.trading_config.Z_SCORE_ENTRY:
                        # Spread too low, long the pair (long stock2, short stock1)  
                        signals.iloc[i, signals.columns.get_loc('signal')] = 1
                        current_position = 1

                # Exit signals
                elif current_position != 0:
                    if abs(z_current) < self.trading_config.Z_SCORE_EXIT:
                        # Close position
                        signals.iloc[i, signals.columns.get_loc('signal')] = -current_position
                        current_position = 0
                    # Stop loss
                    elif abs(z_current) > self.trading_config.STOP_LOSS_MULTIPLIER:
                        signals.iloc[i, signals.columns.get_loc('signal')] = -current_position
                        current_position = 0
                        self.logger.warning(f"Stop loss triggered at z-score: {z_current}")

                signals.iloc[i, signals.columns.get_loc('position')] = current_position

            # Add entry and exit points
            signals['entry'] = (signals['signal'] != 0) & (signals['signal'] != signals['signal'].shift(1))
            signals['exit'] = (signals['signal'] != 0) & (signals['position'].shift(1) != 0)

            return signals

        except Exception as e:
            self.logger.error(f"Error generating trading signals: {str(e)}")
            return pd.DataFrame()

    def analyze_pair(self, symbol1: str, symbol2: str, period: str = "1y") -> dict:
        """
        Complete analysis of a stock pair

        Args:
            symbol1: First stock symbol
            symbol2: Second stock symbol
            period: Data period to analyze

        Returns:
            Complete pair analysis results
        """
        try:
            self.logger.info(f"Analyzing pair: {symbol1} - {symbol2}")

            # Fetch data for both stocks
            data1 = self.fetch_stock_data(symbol1, period)
            data2 = self.fetch_stock_data(symbol2, period)

            if data1.empty or data2.empty:
                return {'error': 'Failed to fetch data for one or both stocks'}

            # Use closing prices
            price1 = data1['Close']
            price2 = data2['Close']

            # Test cointegration
            coint_result = self.test_cointegration(price1, price2)

            if not coint_result['cointegrated']:
                return {
                    'pair': f"{symbol1} - {symbol2}",
                    'cointegrated': False,
                    'reason': f"P-value {coint_result['p_value']:.4f} > {self.pair_config.MAX_COINTEGRATION_PVALUE}"
                }

            # Calculate spread and z-score
            spread = self.calculate_spread(price1, price2, 
                                         coint_result['hedge_ratio'], 
                                         coint_result['intercept'])
            z_score = self.calculate_zscore(spread)

            # Generate trading signals
            signals = self.generate_trading_signals(z_score, spread)

            # Calculate basic statistics
            correlation = price1.corr(price2)
            current_z_score = z_score.iloc[-1] if len(z_score) > 0 else 0

            # Count trading opportunities
            entry_signals = signals['entry'].sum() if not signals.empty else 0

            result = {
                'pair': f"{symbol1} - {symbol2}",
                'symbol1': symbol1,
                'symbol2': symbol2,
                'cointegrated': True,
                'cointegration_details': coint_result,
                'correlation': correlation,
                'current_z_score': current_z_score,
                'spread_mean': spread.mean(),
                'spread_std': spread.std(),
                'signals_count': entry_signals,
                'data_points': len(price1),
                'last_updated': datetime.now().isoformat(),
                'signals': signals.tail(10).to_dict() if not signals.empty else {},  # Last 10 signals
                'current_signal': self._get_current_signal(current_z_score)
            }

            return result

        except Exception as e:
            self.logger.error(f"Error analyzing pair {symbol1}-{symbol2}: {str(e)}")
            return {'error': str(e)}

    def _get_current_signal(self, z_score: float) -> dict:
        """
        Get current trading signal based on z-score

        Args:
            z_score: Current z-score

        Returns:
            Signal dictionary
        """
        if pd.isna(z_score):
            return {'signal': 'NO_DATA', 'strength': 0, 'description': 'No data available'}

        if z_score > self.trading_config.Z_SCORE_ENTRY:
            strength = min(abs(z_score) / self.trading_config.Z_SCORE_ENTRY, 3.0)
            return {
                'signal': 'SHORT_PAIR',
                'strength': strength,
                'description': f'Short pair (z-score: {z_score:.2f})',
                'action': 'Sell stock2, Buy stock1'
            }
        elif z_score < -self.trading_config.Z_SCORE_ENTRY:
            strength = min(abs(z_score) / self.trading_config.Z_SCORE_ENTRY, 3.0)
            return {
                'signal': 'LONG_PAIR',
                'strength': strength,
                'description': f'Long pair (z-score: {z_score:.2f})',
                'action': 'Buy stock2, Sell stock1'
            }
        elif abs(z_score) < self.trading_config.Z_SCORE_EXIT:
            return {
                'signal': 'CLOSE_POSITION',
                'strength': 1.0,
                'description': f'Close position (z-score: {z_score:.2f})',
                'action': 'Mean reversion detected'
            }
        else:
            return {
                'signal': 'HOLD',
                'strength': 0,
                'description': f'Hold current position (z-score: {z_score:.2f})',
                'action': 'No action required'
            }

    def screen_all_pairs(self) -> list:
        """
        Screen all default pairs for cointegration

        Returns:
            List of viable pairs with analysis
        """
        viable_pairs = []

        self.logger.info("Screening all default pairs for cointegration...")

        for symbol1, symbol2 in self.pair_config.DEFAULT_PAIRS:
            try:
                analysis = self.analyze_pair(symbol1, symbol2)

                if analysis.get('cointegrated', False):
                    viable_pairs.append(analysis)
                    self.logger.info(f"✓ Viable pair found: {analysis['pair']} "
                                   f"(p-value: {analysis['cointegration_details']['p_value']:.4f})")
                else:
                    self.logger.info(f"✗ Pair rejected: {symbol1}-{symbol2} "
                                   f"({'Error' if 'error' in analysis else 'Not cointegrated'})")

            except Exception as e:
                self.logger.error(f"Error screening pair {symbol1}-{symbol2}: {str(e)}")

        # Sort by p-value (lower is better)
        viable_pairs.sort(key=lambda x: x.get('cointegration_details', {}).get('p_value', 1.0))

        self.logger.info(f"Found {len(viable_pairs)} viable pairs out of {len(self.pair_config.DEFAULT_PAIRS)}")

        return viable_pairs

    def calculate_position_size(self, price1: float, price2: float, hedge_ratio: float,
                              available_capital: float = None) -> dict:
        """
        Calculate optimal position sizes for a pair trade

        Args:
            price1: Current price of stock1
            price2: Current price of stock2
            hedge_ratio: Hedge ratio from cointegration
            available_capital: Available trading capital

        Returns:
            Position sizing details
        """
        if available_capital is None:
            available_capital = self.pair_config.CAPITAL_PER_PAIR

        # Calculate position sizes based on hedge ratio
        # For a market-neutral position: quantity1 * price1 = hedge_ratio * quantity2 * price2

        # Start with equal dollar amounts
        target_exposure = available_capital * self.trading_config.MAX_POSITION_SIZE

        # Calculate quantities
        # Let quantity2 be base quantity
        # quantity1 = hedge_ratio * quantity2
        # Total cost = (hedge_ratio * price1 + price2) * quantity2

        quantity2 = int(target_exposure / (abs(hedge_ratio) * price1 + price2))
        quantity1 = int(abs(hedge_ratio) * quantity2)

        # Ensure minimum viable quantities
        quantity1 = max(quantity1, 1)
        quantity2 = max(quantity2, 1)

        cost1 = quantity1 * price1
        cost2 = quantity2 * price2
        total_cost = cost1 + cost2

        return {
            'quantity1': quantity1,
            'quantity2': quantity2,
            'cost1': cost1,
            'cost2': cost2,
            'total_cost': total_cost,
            'hedge_ratio': hedge_ratio,
            'capital_utilization': (total_cost / available_capital) * 100
        }

    def validate_trade_profitability(self, symbol1: str, symbol2: str, 
                                   quantity1: int, quantity2: int,
                                   entry_price1: float, entry_price2: float,
                                   exit_price1: float, exit_price2: float,
                                   trade_direction: int) -> dict:
        """
        Validate if a trade would be profitable after all fees

        Args:
            symbol1, symbol2: Stock symbols
            quantity1, quantity2: Position quantities
            entry_price1, entry_price2: Entry prices
            exit_price1, exit_price2: Exit prices
            trade_direction: 1 for long pair, -1 for short pair

        Returns:
            Trade profitability analysis
        """
        try:
            # Calculate fees for both legs of the trade
            if trade_direction > 0:  # Long pair (long stock2, short stock1)
                # Stock1: Short then cover
                fees1 = self.fee_calculator.calculate_total_charges(
                    quantity1, exit_price1, entry_price1, "intraday", "NSE"
                )
                # Stock2: Buy then sell
                fees2 = self.fee_calculator.calculate_total_charges(
                    quantity2, entry_price2, exit_price2, "intraday", "NSE"
                )
            else:  # Short pair (short stock2, long stock1)
                # Stock1: Buy then sell
                fees1 = self.fee_calculator.calculate_total_charges(
                    quantity1, entry_price1, exit_price1, "intraday", "NSE"
                )
                # Stock2: Short then cover  
                fees2 = self.fee_calculator.calculate_total_charges(
                    quantity2, exit_price2, entry_price2, "intraday", "NSE"
                )

            total_fees = fees1['totals']['total_charges'] + fees2['totals']['total_charges']
            gross_profit = fees1['totals']['gross_profit'] + fees2['totals']['gross_profit']
            net_profit = gross_profit - total_fees

            total_investment = (quantity1 * entry_price1) + (quantity2 * entry_price2)
            net_profit_percent = (net_profit / total_investment) * 100

            is_profitable = net_profit_percent >= self.trading_config.MIN_PROFIT_THRESHOLD * 100

            return {
                'is_profitable': is_profitable,
                'gross_profit': gross_profit,
                'total_fees': total_fees,
                'net_profit': net_profit,
                'net_profit_percent': net_profit_percent,
                'total_investment': total_investment,
                'fees_breakdown': {
                    'stock1_fees': fees1['totals']['total_charges'],
                    'stock2_fees': fees2['totals']['total_charges']
                },
                'recommendation': 'EXECUTE' if is_profitable else 'SKIP'
            }

        except Exception as e:
            self.logger.error(f"Error validating trade profitability: {str(e)}")
            return {'error': str(e)}

# Example usage
if __name__ == "__main__":
    engine = StatisticalArbitrageEngine()

    # Test single pair analysis
    print("Testing single pair analysis...")
    result = engine.analyze_pair('RELIANCE.NS', 'ONGC.NS')
    print(f"Analysis result: {result.get('pair', 'Error')}")
    print(f"Cointegrated: {result.get('cointegrated', False)}")
    if result.get('cointegrated'):
        print(f"Current signal: {result.get('current_signal', {}).get('description', 'None')}")

    # Screen all pairs
    print("\nScreening all pairs...")
    viable_pairs = engine.screen_all_pairs()
    print(f"Found {len(viable_pairs)} viable pairs")

    for pair in viable_pairs[:3]:  # Show top 3
        print(f"- {pair['pair']}: p-value={pair['cointegration_details']['p_value']:.4f}, "
              f"current_z_score={pair['current_z_score']:.2f}")
