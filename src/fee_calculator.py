"""
Fee Calculator for Zerodha trading charges
Implements all fees, taxes, and charges as per Zerodha 2025 structure
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

from config import ZerodhaFeeStructure

class ZerodhaFeeCalculator:
    """Calculate all trading fees and taxes for Zerodha"""

    def __init__(self):
        self.fees = ZerodhaFeeStructure()

    def calculate_brokerage(self, quantity: int, price: float, trade_type: str = "intraday") -> float:
        """
        Calculate brokerage charges

        Args:
            quantity: Number of shares
            price: Share price
            trade_type: "delivery" or "intraday"

        Returns:
            Brokerage amount in Rs
        """
        turnover = quantity * price

        if trade_type.lower() == "delivery":
            return 0.0  # Free for delivery
        else:  # intraday
            brokerage_percent = turnover * self.fees.INTRADAY_BROKERAGE_PERCENT
            return min(brokerage_percent, self.fees.INTRADAY_BROKERAGE_MAX)

    def calculate_stt(self, quantity: int, buy_price: float, sell_price: float, trade_type: str = "intraday") -> float:
        """
        Calculate Securities Transaction Tax (STT)

        Args:
            quantity: Number of shares
            buy_price: Purchase price per share
            sell_price: Selling price per share
            trade_type: "delivery" or "intraday"

        Returns:
            STT amount in Rs
        """
        if trade_type.lower() == "delivery":
            # STT on both buy and sell for delivery
            buy_turnover = quantity * buy_price
            sell_turnover = quantity * sell_price

            stt_buy = buy_turnover * self.fees.STT_DELIVERY_BUY
            stt_sell = sell_turnover * self.fees.STT_DELIVERY_SELL

            return stt_buy + stt_sell
        else:  # intraday
            # STT only on sell side for intraday
            sell_turnover = quantity * sell_price
            return sell_turnover * self.fees.STT_INTRADAY_SELL

    def calculate_transaction_charges(self, quantity: int, price: float, exchange: str = "NSE") -> float:
        """
        Calculate exchange transaction charges

        Args:
            quantity: Number of shares
            price: Share price
            exchange: "NSE" or "BSE"

        Returns:
            Transaction charges in Rs
        """
        turnover = quantity * price

        if exchange.upper() == "NSE":
            return turnover * self.fees.NSE_TRANSACTION_CHARGES
        else:  # BSE
            return turnover * self.fees.BSE_TRANSACTION_CHARGES

    def calculate_sebi_charges(self, quantity: int, price: float) -> float:
        """
        Calculate SEBI charges

        Args:
            quantity: Number of shares
            price: Share price

        Returns:
            SEBI charges in Rs
        """
        turnover = quantity * price
        return turnover * self.fees.SEBI_CHARGES

    def calculate_stamp_duty(self, quantity: int, price: float, trade_type: str = "intraday") -> float:
        """
        Calculate stamp duty (only on buy side)

        Args:
            quantity: Number of shares
            price: Share price
            trade_type: "delivery" or "intraday"

        Returns:
            Stamp duty in Rs
        """
        turnover = quantity * price

        if trade_type.lower() == "delivery":
            return turnover * self.fees.STAMP_DUTY_DELIVERY
        else:  # intraday
            return turnover * self.fees.STAMP_DUTY_INTRADAY

    def calculate_gst(self, brokerage: float, transaction_charges: float) -> float:
        """
        Calculate GST on brokerage and transaction charges

        Args:
            brokerage: Brokerage amount
            transaction_charges: Exchange transaction charges

        Returns:
            GST amount in Rs
        """
        taxable_amount = brokerage + transaction_charges
        return taxable_amount * self.fees.GST_RATE

    def calculate_total_charges(self, quantity: int, buy_price: float, sell_price: float, 
                              trade_type: str = "intraday", exchange: str = "NSE",
                              include_dp_charges: bool = False) -> dict:
        """
        Calculate all charges for a complete trade

        Args:
            quantity: Number of shares
            buy_price: Purchase price per share
            sell_price: Selling price per share
            trade_type: "delivery" or "intraday"
            exchange: "NSE" or "BSE"
            include_dp_charges: Whether to include DP charges (for selling from demat)

        Returns:
            Dictionary with breakdown of all charges
        """
        # Calculate individual charges
        brokerage_buy = self.calculate_brokerage(quantity, buy_price, trade_type)
        brokerage_sell = self.calculate_brokerage(quantity, sell_price, trade_type)
        total_brokerage = brokerage_buy + brokerage_sell

        stt = self.calculate_stt(quantity, buy_price, sell_price, trade_type)

        transaction_charges_buy = self.calculate_transaction_charges(quantity, buy_price, exchange)
        transaction_charges_sell = self.calculate_transaction_charges(quantity, sell_price, exchange)
        total_transaction_charges = transaction_charges_buy + transaction_charges_sell

        sebi_charges_buy = self.calculate_sebi_charges(quantity, buy_price)
        sebi_charges_sell = self.calculate_sebi_charges(quantity, sell_price)
        total_sebi_charges = sebi_charges_buy + sebi_charges_sell

        stamp_duty = self.calculate_stamp_duty(quantity, buy_price, trade_type)

        gst = self.calculate_gst(total_brokerage, total_transaction_charges)

        dp_charges = self.fees.DP_CHARGES if include_dp_charges else 0.0

        # Calculate totals
        total_charges = (total_brokerage + stt + total_transaction_charges + 
                        total_sebi_charges + stamp_duty + gst + dp_charges)

        # Calculate net profit/loss
        gross_profit = (sell_price - buy_price) * quantity
        net_profit = gross_profit - total_charges

        return {
            "breakdown": {
                "brokerage": round(total_brokerage, 2),
                "stt": round(stt, 2),
                "transaction_charges": round(total_transaction_charges, 2),
                "sebi_charges": round(total_sebi_charges, 2),
                "stamp_duty": round(stamp_duty, 2),
                "gst": round(gst, 2),
                "dp_charges": round(dp_charges, 2)
            },
            "totals": {
                "total_charges": round(total_charges, 2),
                "gross_profit": round(gross_profit, 2),
                "net_profit": round(net_profit, 2),
                "net_profit_percent": round((net_profit / (quantity * buy_price)) * 100, 3)
            },
            "trade_details": {
                "quantity": quantity,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "buy_value": quantity * buy_price,
                "sell_value": quantity * sell_price,
                "trade_type": trade_type,
                "exchange": exchange
            }
        }

    def is_trade_profitable(self, quantity: int, buy_price: float, sell_price: float, 
                           min_profit_percent: float = 0.1, trade_type: str = "intraday",
                           exchange: str = "NSE") -> tuple:
        """
        Check if a trade would be profitable after all charges

        Args:
            quantity: Number of shares
            buy_price: Purchase price per share
            sell_price: Selling price per share
            min_profit_percent: Minimum profit percentage required
            trade_type: "delivery" or "intraday"
            exchange: "NSE" or "BSE"

        Returns:
            Tuple of (is_profitable: bool, net_profit: float, profit_percent: float)
        """
        charges = self.calculate_total_charges(quantity, buy_price, sell_price, 
                                             trade_type, exchange)

        net_profit = charges["totals"]["net_profit"]
        profit_percent = charges["totals"]["net_profit_percent"]

        is_profitable = profit_percent >= min_profit_percent

        return is_profitable, net_profit, profit_percent

    def get_minimum_profitable_price(self, quantity: int, buy_price: float, 
                                   min_profit_percent: float = 0.1, 
                                   trade_type: str = "intraday",
                                   exchange: str = "NSE") -> float:
        """
        Calculate minimum selling price for profitable trade

        Args:
            quantity: Number of shares
            buy_price: Purchase price per share
            min_profit_percent: Minimum profit percentage required
            trade_type: "delivery" or "intraday"
            exchange: "NSE" or "BSE"

        Returns:
            Minimum selling price for profitable trade
        """
        # Start with a rough estimate and iterate
        sell_price = buy_price * 1.01  # Start with 1% higher

        for _ in range(100):  # Maximum iterations
            is_profitable, _, profit_percent = self.is_trade_profitable(
                quantity, buy_price, sell_price, min_profit_percent, trade_type, exchange
            )

            if is_profitable:
                if profit_percent > min_profit_percent + 0.01:  # Too much profit, reduce
                    sell_price -= 0.01
                else:  # Close enough
                    break
            else:  # Not profitable yet, increase
                sell_price += 0.01

        return round(sell_price, 2)

# Example usage and testing
if __name__ == "__main__":
    calculator = ZerodhaFeeCalculator()

    # Test example
    result = calculator.calculate_total_charges(
        quantity=100,
        buy_price=1500.0,
        sell_price=1515.0,
        trade_type="intraday",
        exchange="NSE"
    )

    print("Fee Calculation Example:")
    print("=" * 50)
    print(f"Quantity: {result['trade_details']['quantity']}")
    print(f"Buy Price: Rs {result['trade_details']['buy_price']}")
    print(f"Sell Price: Rs {result['trade_details']['sell_price']}")
    print(f"Buy Value: Rs {result['trade_details']['buy_value']}")
    print(f"Sell Value: Rs {result['trade_details']['sell_value']}")
    print("\nCharges Breakdown:")
    print("-" * 30)
    for charge, amount in result['breakdown'].items():
        print(f"{charge.replace('_', ' ').title()}: Rs {amount}")

    print("\nTotals:")
    print("-" * 30)
    print(f"Total Charges: Rs {result['totals']['total_charges']}")
    print(f"Gross Profit: Rs {result['totals']['gross_profit']}")
    print(f"Net Profit: Rs {result['totals']['net_profit']}")
    print(f"Net Profit %: {result['totals']['net_profit_percent']}%")

    # Test profitability check
    is_profitable, net_profit, profit_percent = calculator.is_trade_profitable(
        100, 1500.0, 1515.0, min_profit_percent=0.1
    )
    print(f"\nIs Trade Profitable (min 0.1%): {is_profitable}")
    print(f"Net Profit: Rs {net_profit}")
    print(f"Profit Percentage: {profit_percent}%")
