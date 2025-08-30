# Statistical Arbitrage Trading System

A comprehensive statistical arbitrage trading system for Indian stock markets with integrated Zerodha fee calculations, risk management, and a real-time Tkinter dashboard.

## 🚀 Features

### Core Functionality
- **Statistical Arbitrage Engine**: Advanced pair trading using cointegration analysis
- **Real-time Monitoring**: Live price updates and signal generation
- **Risk Management**: Built-in position sizing and stop-loss mechanisms
- **Fee Integration**: Complete Zerodha fee structure with all taxes and charges
- **Profit Validation**: Ensures trades are profitable after all costs

### Dashboard Features
- **📊 Overview Tab**: Key metrics, portfolio performance, and system controls
- **📈 Pairs Analysis**: Interactive pair selection with cointegration statistics
- **📡 Signals Tab**: Real-time trading signals with confidence ratings
- **💰 Trades Tab**: Position management and trade history
- **⚙️ Settings Tab**: Configuration, fee calculator, and logging

### Technical Features
- **Cointegration Testing**: Engle-Granger two-step method
- **Z-Score Analysis**: Dynamic spread analysis with rolling statistics
- **Position Sizing**: Automated capital allocation and risk management
- **Fee Calculation**: Complete Zerodha charge structure (STT, brokerage, GST, etc.)
- **Data Integration**: Yahoo Finance (yfinance) with Kite API ready

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- Windows 10/11, macOS 10.14+, or Linux
- Minimum 4GB RAM
- Internet connection for live data

### Python Dependencies
```
pandas>=1.5.0
numpy>=1.21.0
yfinance>=0.2.0
matplotlib>=3.5.0
seaborn>=0.11.0
scipy>=1.9.0
statsmodels>=0.13.0
scikit-learn>=1.1.0
python-dotenv>=0.19.0
requests>=2.28.0
pytz>=2022.1
```

## 🔧 Installation

### 1. Clone/Download the Repository
```bash
# If you have git
git clone <repository-url>
cd statistical_arbitrage

# Or download and extract the ZIP file
```

### 2. Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Or install individually
pip install pandas numpy yfinance matplotlib seaborn scipy statsmodels scikit-learn python-dotenv requests pytz
```

### 3. Verify Installation
```bash
python main.py
```

## 🚀 Quick Start

### 1. Launch the Application
```bash
python main.py
```

### 2. Screen for Viable Pairs
1. Click **"Screen Pairs"** button in the Overview tab
2. Wait for the system to analyze all default stock pairs
3. View results in the **"Pairs Analysis"** tab

### 3. Start Monitoring
1. Click **"Start Monitoring"** to enable real-time updates
2. Check the **"Signals"** tab for trading opportunities
3. Use **"Paper Trade"** to test strategies without real money

### 4. Analyze Fees
1. Go to **"Settings"** tab
2. Use the **"Fee Calculator"** to understand trading costs
3. Adjust parameters based on your risk tolerance

## 📊 Default Stock Pairs

The system analyzes these Indian stock pairs by default:

| Sector | Pair 1 | Pair 2 |
|---------|---------|---------|
| Energy | RELIANCE.NS | ONGC.NS |
| Banking | HDFCBANK.NS | KOTAKBANK.NS |
| IT Services | TCS.NS | INFY.NS |
| Banking | ICICIBANK.NS | SBIN.NS |
| FMCG | HINDUNILVR.NS | ITC.NS |
| Financial Services | BAJFINANCE.NS | HDFCLIFE.NS |
| Automobiles | MARUTI.NS | M&M.NS |
| Paints | ASIANPAINT.NS | BERGER.NS |

## ⚙️ Configuration

### Trading Parameters
Located in `config/config.py`:

```python
# Entry/Exit thresholds
Z_SCORE_ENTRY = 2.0          # Enter trade when |z-score| > 2.0
Z_SCORE_EXIT = 0.5           # Exit trade when |z-score| < 0.5

# Risk management
MAX_POSITION_SIZE = 0.02     # 2% of portfolio per position
STOP_LOSS_MULTIPLIER = 2.5   # Stop loss at 2.5 std deviations

# Capital allocation
CAPITAL_PER_PAIR = 100000    # ₹1 lakh per pair
```

### Zerodha Fee Structure (2025)
- **Delivery**: Free brokerage
- **Intraday**: 0.03% or ₹20 max per order
- **STT**: 0.025% (intraday), 0.1% (delivery)
- **Exchange charges**: NSE ₹297/crore, BSE ₹375/crore
- **GST**: 18% on brokerage + transaction charges

## 📈 How It Works

### 1. Cointegration Analysis
- Tests pairs for long-term statistical relationship
- Uses Engle-Granger two-step method
- Requires p-value < 0.05 for viability

### 2. Spread Calculation
```
Spread = Stock2 - (Hedge_Ratio × Stock1 + Intercept)
```

### 3. Z-Score Trading Signals
```
Z-Score = (Current_Spread - Rolling_Mean) / Rolling_StdDev

Entry Signals:
- Z-Score > +2.0: Short the pair (sell stock2, buy stock1)
- Z-Score < -2.0: Long the pair (buy stock2, sell stock1)

Exit Signals:
- |Z-Score| < 0.5: Close position (mean reversion)
```

### 4. Risk Management
- Position sizing based on available capital
- Stop-loss at extreme z-score levels
- Profit validation after all fees

## 💰 Fee Calculation Example

For a ₹1,50,000 intraday trade:

| Component | Calculation | Amount |
|-----------|------------|---------|
| Brokerage | min(0.03% × ₹1,50,000, ₹20) | ₹20.00 |
| STT | 0.025% × ₹1,50,000 | ₹37.50 |
| Exchange Charges | ₹297/crore × ₹1,50,000 | ₹4.46 |
| SEBI Charges | ₹10/crore × ₹1,50,000 | ₹0.15 |
| GST | 18% × (₹20 + ₹4.46) | ₹4.40 |
| **Total Charges** |  | **₹66.51** |

## 📱 Dashboard Usage

### Overview Tab
- **Key Metrics**: Real-time portfolio statistics
- **Controls**: Start/stop monitoring, refresh data
- **Status**: System status and last update time

### Pairs Analysis Tab
- **Pairs List**: All viable pairs with statistics
- **Pair Details**: Selected pair analysis and charts
- **Cointegration Info**: P-values, hedge ratios, correlations

### Signals Tab
- **Current Signals**: Live trading opportunities
- **Signal Actions**: Execute, paper trade, or calculate positions
- **Signal Log**: Historical signal activity

### Trades Tab
- **Current Positions**: Open trades and P&L
- **Trade History**: Completed trades with performance
- **Export**: Save trade data to CSV

### Settings Tab
- **Trading Parameters**: Adjust z-score thresholds and risk limits
- **Fee Calculator**: Calculate costs for any trade size
- **Logging**: System activity and error logs

## 🔄 Transitioning to Kite API

Currently uses Yahoo Finance (yfinance). To switch to Kite API:

1. **Get Kite Connect credentials**:
   - API Key and Secret from Zerodha Console
   - Generate access token

2. **Update configuration**:
   ```python
   # In config/config.py
   API_KEY = "your_api_key"
   API_SECRET = "your_api_secret"
   ```

3. **Replace data fetching**:
   - Modify `fetch_stock_data()` in `stat_arb_engine.py`
   - Use Kite Connect instead of yfinance

4. **Add order execution**:
   - Implement actual trade execution
   - Add order management functions

## ⚠️ Risk Warnings

### Market Risks
- **Cointegration breakdown**: Pairs can lose statistical relationship
- **Market volatility**: Extreme events can cause large losses
- **Liquidity risk**: Low liquidity can prevent timely exits

### Technical Risks
- **Data delays**: Network issues can cause stale data
- **System failures**: Software bugs or crashes
- **API limits**: Rate limiting from data providers

### Regulatory Compliance
- **SEBI approval**: High-frequency strategies may need approval
- **Tax implications**: Short-term capital gains tax applies
- **Margin requirements**: Ensure sufficient margin for positions

## 🔧 Troubleshooting

### Common Issues

**1. "No data found for symbol" Error**
- Check internet connection
- Verify stock symbol format (e.g., RELIANCE.NS)
- Try different time periods

**2. "Insufficient data for cointegration" Warning**
- Increase lookback period in settings
- Check if stocks were recently listed
- Verify both stocks have trading history

**3. Dashboard not updating**
- Restart monitoring
- Check log files for errors
- Verify yfinance package version

**4. Import errors on startup**
- Run: `pip install -r requirements.txt`
- Check Python version (3.8+ required)
- Verify all dependencies installed

### Log Files
- **System logs**: `logs/stat_arb.log`
- **Error debugging**: Check console output
- **Trade logs**: Stored in dashboard memory (export to save)

## 📚 Additional Resources

### Statistical Arbitrage Theory
- [Pairs Trading Research](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=141615)
- [Cointegration Testing](https://www.statsmodels.org/stable/examples/notebooks/generated/tsa_engle_granger_two_step_cointegration_test.html)

### Indian Market Regulations
- [SEBI Algorithmic Trading Guidelines](https://www.sebi.gov.in/legal/circulars/apr-2012/circular-on-algorithmic-trading_23176.html)
- [Zerodha Trading Charges](https://zerodha.com/charges/)

### Python Libraries
- [yfinance Documentation](https://pypi.org/project/yfinance/)
- [statsmodels](https://www.statsmodels.org/)
- [scikit-learn](https://scikit-learn.org/)

## 🤝 Support

### Getting Help
1. Check the troubleshooting section above
2. Review log files for specific errors
3. Ensure all dependencies are properly installed
4. Test with smaller datasets first

### Contributing
- Report bugs via issue tracking
- Suggest feature improvements
- Submit pull requests for enhancements

## 📄 License

This project is for educational and research purposes. 

**Disclaimer**: This software is provided for educational purposes only. Trading involves risk of financial loss. The authors are not responsible for any financial losses incurred through use of this software. Always consult with qualified financial advisors before making investment decisions.

## 🔮 Future Enhancements

### Planned Features
- **Kite API Integration**: Direct broker connectivity
- **Machine Learning**: Enhanced signal generation
- **Multiple Timeframes**: Intraday and swing trading modes
- **Portfolio Optimization**: Multi-pair portfolio management
- **Advanced Charts**: Technical analysis indicators
- **Mobile App**: React Native companion app

### Advanced Strategies
- **Mean Reversion**: Beyond pair trading
- **Momentum Strategies**: Trend following additions
- **Options Integration**: Pairs trading with derivatives
- **Sector Rotation**: Cross-sector statistical arbitrage

---

**Happy Trading! 📈**

*Remember: Past performance does not guarantee future results. Always trade responsibly and within your risk tolerance.*
