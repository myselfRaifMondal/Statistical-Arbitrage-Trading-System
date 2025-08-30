"""
Statistical Arbitrage Dashboard - Tkinter GUI Application
Main interface for monitoring and controlling the trading system
"""

from tkinter import *
import tkinter
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import threading
import time
from datetime import datetime
import sys
import os
import queue
import json

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.config import TradingConfig, PairTradingConfig
from src.stat_arb_engine import StatisticalArbitrageEngine
from src.fee_calculator import ZerodhaFeeCalculator

class StatisticalArbitrageDashboard:
    """Main dashboard application"""

    def __init__(self, root):
        self.root = root
        self.root.title("Statistical Arbitrage Trading Dashboard")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')

        # Initialize components
        self.engine = StatisticalArbitrageEngine()
        self.fee_calculator = ZerodhaFeeCalculator()
        self.trading_config = TradingConfig()
        self.pair_config = PairTradingConfig()

        # Data storage
        self.viable_pairs = []
        self.selected_pair_data = None
        self.log_queue = queue.Queue()
        self.is_monitoring = False
        self.monitoring_thread = None

        # Setup GUI
        self.setup_gui()
        self.setup_logging()

        # Start with pair screening
        self.update_status("Ready - Click 'Screen Pairs' to begin analysis")

    def setup_gui(self):
        """Setup the main GUI components"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_overview_tab()
        self.create_pairs_tab()
        self.create_signals_tab()
        self.create_trades_tab()
        self.create_settings_tab()

        # Status bar
        self.status_frame = Frame(self.root, relief=SUNKEN, bd=1)
        self.status_frame.pack(side=BOTTOM, fill=X)
        self.status_label = Label(self.status_frame, text="Initializing...", anchor=W)
        self.status_label.pack(side=LEFT, padx=5)

        # Real-time clock
        self.clock_label = Label(self.status_frame, text="", anchor=E)
        self.clock_label.pack(side=RIGHT, padx=5)
        self.update_clock()

    def create_overview_tab(self):
        """Create overview tab with key metrics"""
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="📊 Overview")

        # Main metrics frame
        metrics_frame = ttk.LabelFrame(self.overview_frame, text="Key Metrics", padding=10)
        metrics_frame.pack(fill=X, padx=10, pady=5)

        # Create metrics display
        self.metrics_vars = {
            'total_pairs': StringVar(value="0"),
            'active_pairs': StringVar(value="0"),
            'total_signals': StringVar(value="0"),
            'profit_loss': StringVar(value="₹0.00"),
            'win_rate': StringVar(value="0%"),
            'last_update': StringVar(value="Never")
        }

        # Metrics grid
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=X)

        row = 0
        for i, (key, var) in enumerate(self.metrics_vars.items()):
            col = i % 3
            if col == 0 and i > 0:
                row += 1

            label_text = key.replace('_', ' ').title()
            ttk.Label(metrics_grid, text=f"{label_text}:", font=('Arial', 10, 'bold')).grid(
                row=row*2, column=col, sticky='w', padx=10, pady=2)
            ttk.Label(metrics_grid, textvariable=var, font=('Arial', 12)).grid(
                row=row*2+1, column=col, sticky='w', padx=10, pady=2)

        # Control buttons
        control_frame = ttk.LabelFrame(self.overview_frame, text="Controls", padding=10)
        control_frame.pack(fill=X, padx=10, pady=5)

        button_frame = ttk.Frame(control_frame)
        button_frame.pack()

        self.screen_button = ttk.Button(button_frame, text="Screen Pairs", 
                                       command=self.screen_pairs_threaded,
                                       style='Accent.TButton')
        self.screen_button.pack(side=LEFT, padx=5)

        self.monitor_button = ttk.Button(button_frame, text="Start Monitoring",
                                        command=self.toggle_monitoring)
        self.monitor_button.pack(side=LEFT, padx=5)

        ttk.Button(button_frame, text="Refresh Data", 
                  command=self.refresh_data).pack(side=LEFT, padx=5)

        ttk.Button(button_frame, text="Export Data", 
                  command=self.export_data).pack(side=LEFT, padx=5)

        # Market overview chart placeholder
        chart_frame = ttk.LabelFrame(self.overview_frame, text="Market Overview", padding=10)
        chart_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.overview_chart_frame = ttk.Frame(chart_frame)
        self.overview_chart_frame.pack(fill=BOTH, expand=True)

    def create_pairs_tab(self):
        """Create pairs analysis tab"""
        self.pairs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.pairs_frame, text="📈 Pairs Analysis")

        # Pairs list frame
        list_frame = ttk.LabelFrame(self.pairs_frame, text="Viable Pairs", padding=10)
        list_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 5), pady=10)

        # Pairs treeview
        columns = ('Pair', 'P-Value', 'Correlation', 'Z-Score', 'Signal', 'Status')
        self.pairs_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)

        # Configure columns
        column_widths = {'Pair': 120, 'P-Value': 80, 'Correlation': 80, 
                        'Z-Score': 80, 'Signal': 100, 'Status': 80}

        for col in columns:
            self.pairs_tree.heading(col, text=col)
            self.pairs_tree.column(col, width=column_widths.get(col, 100))

        # Scrollbars for treeview
        pairs_scroll_y = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.pairs_tree.yview)
        pairs_scroll_x = ttk.Scrollbar(list_frame, orient=HORIZONTAL, command=self.pairs_tree.xview)
        self.pairs_tree.configure(yscrollcommand=pairs_scroll_y.set, xscrollcommand=pairs_scroll_x.set)

        self.pairs_tree.pack(side=LEFT, fill=BOTH, expand=True)
        pairs_scroll_y.pack(side=RIGHT, fill=Y)
        pairs_scroll_x.pack(side=BOTTOM, fill=X)

        # Bind selection event
        self.pairs_tree.bind('<<TreeviewSelect>>', self.on_pair_select)

        # Pair details frame
        details_frame = ttk.LabelFrame(self.pairs_frame, text="Pair Details", padding=10)
        details_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(5, 10), pady=10)

        # Pair info
        info_frame = ttk.Frame(details_frame)
        info_frame.pack(fill=X, pady=(0, 10))

        self.pair_info_vars = {
            'selected_pair': StringVar(value="No pair selected"),
            'cointegration_p': StringVar(value="--"),
            'hedge_ratio': StringVar(value="--"),
            'correlation': StringVar(value="--"),
            'current_zscore': StringVar(value="--"),
            'signal_strength': StringVar(value="--")
        }

        for i, (key, var) in enumerate(self.pair_info_vars.items()):
            label_text = key.replace('_', ' ').title()
            ttk.Label(info_frame, text=f"{label_text}:", font=('Arial', 9, 'bold')).grid(
                row=i, column=0, sticky='w', pady=2)
            ttk.Label(info_frame, textvariable=var, font=('Arial', 9)).grid(
                row=i, column=1, sticky='w', padx=10, pady=2)

        # Chart placeholder
        self.pair_chart_frame = ttk.Frame(details_frame)
        self.pair_chart_frame.pack(fill=BOTH, expand=True)

    def create_signals_tab(self):
        """Create trading signals tab"""
        self.signals_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.signals_frame, text="📡 Signals")

        # Current signals frame
        current_frame = ttk.LabelFrame(self.signals_frame, text="Current Signals", padding=10)
        current_frame.pack(fill=X, padx=10, pady=(10, 5))

        # Signals treeview
        signal_columns = ('Time', 'Pair', 'Signal', 'Z-Score', 'Action', 'Confidence')
        self.signals_tree = ttk.Treeview(current_frame, columns=signal_columns, 
                                        show='headings', height=8)

        for col in signal_columns:
            self.signals_tree.heading(col, text=col)
            self.signals_tree.column(col, width=100)

        signals_scroll = ttk.Scrollbar(current_frame, orient=VERTICAL, 
                                     command=self.signals_tree.yview)
        self.signals_tree.configure(yscrollcommand=signals_scroll.set)

        self.signals_tree.pack(side=LEFT, fill=BOTH, expand=True)
        signals_scroll.pack(side=RIGHT, fill=Y)

        # Signal details and actions
        actions_frame = ttk.LabelFrame(self.signals_frame, text="Signal Actions", padding=10)
        actions_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Action buttons
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack(fill=X, pady=(0, 10))

        ttk.Button(btn_frame, text="Execute Signal", 
                  command=self.execute_signal).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Paper Trade", 
                  command=self.paper_trade).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Calculate Position", 
                  command=self.calculate_position).pack(side=LEFT, padx=5)

        # Signal log
        log_label = ttk.Label(actions_frame, text="Signal Log:", font=('Arial', 10, 'bold'))
        log_label.pack(anchor='w')

        self.signal_log = scrolledtext.ScrolledText(actions_frame, height=10, 
                                                   font=('Consolas', 9))
        self.signal_log.pack(fill=BOTH, expand=True, pady=(5, 0))

    def create_trades_tab(self):
        """Create trades management tab"""
        self.trades_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trades_frame, text="💰 Trades")

        # Position summary
        position_frame = ttk.LabelFrame(self.trades_frame, text="Current Positions", padding=10)
        position_frame.pack(fill=X, padx=10, pady=(10, 5))

        # Positions treeview
        pos_columns = ('Pair', 'Direction', 'Entry Time', 'Entry Price', 'Current PnL', 
                      'Status', 'Actions')
        self.positions_tree = ttk.Treeview(position_frame, columns=pos_columns, 
                                         show='headings', height=6)

        for col in pos_columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=100)

        pos_scroll = ttk.Scrollbar(position_frame, orient=VERTICAL, 
                                 command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=pos_scroll.set)

        self.positions_tree.pack(side=LEFT, fill=BOTH, expand=True)
        pos_scroll.pack(side=RIGHT, fill=Y)

        # Trade history
        history_frame = ttk.LabelFrame(self.trades_frame, text="Trade History", padding=10)
        history_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # History controls
        hist_controls = ttk.Frame(history_frame)
        hist_controls.pack(fill=X, pady=(0, 10))

        ttk.Label(hist_controls, text="Filter:").pack(side=LEFT)
        self.history_filter = ttk.Combobox(hist_controls, values=['All', 'Today', 'This Week', 
                                                                 'This Month'], state='readonly')
        self.history_filter.set('Today')
        self.history_filter.pack(side=LEFT, padx=5)

        ttk.Button(hist_controls, text="Refresh", 
                  command=self.refresh_trade_history).pack(side=LEFT, padx=5)
        ttk.Button(hist_controls, text="Export", 
                  command=self.export_trades).pack(side=LEFT, padx=5)

        # History treeview
        hist_columns = ('Time', 'Pair', 'Type', 'Quantity', 'Price', 'Fees', 'PnL', 'Status')
        self.history_tree = ttk.Treeview(history_frame, columns=hist_columns, 
                                       show='headings', height=12)

        for col in hist_columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=90)

        hist_scroll = ttk.Scrollbar(history_frame, orient=VERTICAL, 
                                  command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=hist_scroll.set)

        self.history_tree.pack(side=LEFT, fill=BOTH, expand=True)
        hist_scroll.pack(side=RIGHT, fill=Y)

        # Load some sample data
        self.load_sample_trade_data()

    def create_settings_tab(self):
        """Create settings and configuration tab"""
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="⚙️ Settings")

        # Trading parameters
        trading_frame = ttk.LabelFrame(self.settings_frame, text="Trading Parameters", padding=10)
        trading_frame.pack(fill=X, padx=10, pady=(10, 5))

        # Parameters grid
        params_frame = ttk.Frame(trading_frame)
        params_frame.pack(fill=X)

        self.settings_vars = {
            'z_score_entry': DoubleVar(value=self.trading_config.Z_SCORE_ENTRY),
            'z_score_exit': DoubleVar(value=self.trading_config.Z_SCORE_EXIT),
            'stop_loss_multiplier': DoubleVar(value=self.trading_config.STOP_LOSS_MULTIPLIER),
            'min_profit_threshold': DoubleVar(value=self.trading_config.MIN_PROFIT_THRESHOLD * 100),
            'max_position_size': DoubleVar(value=self.trading_config.MAX_POSITION_SIZE * 100),
            'rolling_window': IntVar(value=self.trading_config.ROLLING_WINDOW)
        }

        row = 0
        for key, var in self.settings_vars.items():
            label_text = key.replace('_', ' ').title()
            ttk.Label(params_frame, text=f"{label_text}:").grid(row=row, column=0, sticky='w', pady=5)

            entry = ttk.Entry(params_frame, textvariable=var, width=10)
            entry.grid(row=row, column=1, padx=10, pady=5)

            row += 1

        # Buttons
        ttk.Button(params_frame, text="Save Settings", 
                  command=self.save_settings).grid(row=row, column=0, pady=10)
        ttk.Button(params_frame, text="Reset Defaults", 
                  command=self.reset_settings).grid(row=row, column=1, padx=10, pady=10)

        # Fee calculator
        fee_frame = ttk.LabelFrame(self.settings_frame, text="Fee Calculator", padding=10)
        fee_frame.pack(fill=X, padx=10, pady=5)

        # Fee calculator inputs
        calc_frame = ttk.Frame(fee_frame)
        calc_frame.pack(fill=X)

        self.fee_vars = {
            'quantity': IntVar(value=100),
            'buy_price': DoubleVar(value=1500.0),
            'sell_price': DoubleVar(value=1510.0)
        }

        col = 0
        for key, var in self.fee_vars.items():
            ttk.Label(calc_frame, text=f"{key.replace('_', ' ').title()}:").grid(
                row=0, column=col, padx=5)
            ttk.Entry(calc_frame, textvariable=var, width=10).grid(
                row=1, column=col, padx=5)
            col += 1

        ttk.Button(calc_frame, text="Calculate Fees", 
                  command=self.calculate_fees).grid(row=2, column=1, pady=10)

        # Fee results
        self.fee_result_text = scrolledtext.ScrolledText(fee_frame, height=8, 
                                                        font=('Consolas', 9))
        self.fee_result_text.pack(fill=X, pady=(10, 0))

        # Logging controls
        log_frame = ttk.LabelFrame(self.settings_frame, text="Logging", padding=10)
        log_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Log display
        self.log_display = scrolledtext.ScrolledText(log_frame, height=10, 
                                                    font=('Consolas', 9))
        self.log_display.pack(fill=BOTH, expand=True)

    def setup_logging(self):
        """Setup logging display"""
        self.update_log_display()

    def update_log_display(self):
        """Update log display with recent messages"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_display.insert(END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
                self.log_display.see(END)
        except queue.Empty:
            pass

        # Schedule next update
        self.root.after(1000, self.update_log_display)

    def screen_pairs_threaded(self):
        """Screen pairs in a separate thread"""
        if hasattr(self, 'screening_thread') and self.screening_thread.is_alive():
            messagebox.showinfo("Info", "Pair screening already in progress...")
            return

        self.screen_button.configure(state='disabled', text="Screening...")
        self.update_status("Screening pairs for cointegration...")

        self.screening_thread = threading.Thread(target=self.screen_pairs_worker)
        self.screening_thread.start()

    def screen_pairs_worker(self):
        """Worker function for pair screening"""
        try:
            self.viable_pairs = self.engine.screen_all_pairs()

            # Update GUI in main thread
            self.root.after(0, self.update_pairs_display)
            self.root.after(0, lambda: self.screen_button.configure(
                state='normal', text="Screen Pairs"))
            self.root.after(0, lambda: self.update_status(
                f"Found {len(self.viable_pairs)} viable pairs"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Screening failed: {str(e)}"))
            self.root.after(0, lambda: self.screen_button.configure(
                state='normal', text="Screen Pairs"))

    def update_pairs_display(self):
        """Update pairs treeview with results"""
        # Clear existing items
        for item in self.pairs_tree.get_children():
            self.pairs_tree.delete(item)

        # Add viable pairs
        for pair_data in self.viable_pairs:
            p_value = pair_data['cointegration_details']['p_value']
            correlation = pair_data['correlation']
            z_score = pair_data['current_z_score']
            signal = pair_data['current_signal']['signal']

            self.pairs_tree.insert('', 'end', values=(
                pair_data['pair'],
                f"{p_value:.4f}",
                f"{correlation:.3f}",
                f"{z_score:.2f}",
                signal,
                "Active"
            ))

        # Update metrics
        self.metrics_vars['total_pairs'].set(str(len(self.viable_pairs)))
        self.metrics_vars['last_update'].set(datetime.now().strftime("%H:%M:%S"))

    def on_pair_select(self, event):
        """Handle pair selection in treeview"""
        selection = self.pairs_tree.selection()
        if not selection:
            return

        item = self.pairs_tree.item(selection[0])
        pair_name = item['values'][0]

        # Find selected pair data
        self.selected_pair_data = None
        for pair in self.viable_pairs:
            if pair['pair'] == pair_name:
                self.selected_pair_data = pair
                break

        if self.selected_pair_data:
            self.update_pair_details()

    def update_pair_details(self):
        """Update pair details display"""
        if not self.selected_pair_data:
            return

        # Update info variables
        self.pair_info_vars['selected_pair'].set(self.selected_pair_data['pair'])
        self.pair_info_vars['cointegration_p'].set(
            f"{self.selected_pair_data['cointegration_details']['p_value']:.4f}")
        self.pair_info_vars['hedge_ratio'].set(
            f"{self.selected_pair_data['cointegration_details']['hedge_ratio']:.3f}")
        self.pair_info_vars['correlation'].set(
            f"{self.selected_pair_data['correlation']:.3f}")
        self.pair_info_vars['current_zscore'].set(
            f"{self.selected_pair_data['current_z_score']:.2f}")
        self.pair_info_vars['signal_strength'].set(
            f"{self.selected_pair_data['current_signal']['strength']:.1f}")

        # Update chart (placeholder for now)
        self.plot_pair_chart()

    def plot_pair_chart(self):
        """Plot pair analysis chart"""
        # Clear existing chart
        for widget in self.pair_chart_frame.winfo_children():
            widget.destroy()

        if not self.selected_pair_data:
            return

        # Create matplotlib figure
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)

        # Plot placeholder data (you can extend this with real spread data)
        x = range(50)
        y = [np.sin(i/10) + np.random.normal(0, 0.1) for i in x]
        ax.plot(x, y, 'b-', alpha=0.7, label='Spread')
        ax.axhline(y=2, color='r', linestyle='--', alpha=0.7, label='Entry Threshold')
        ax.axhline(y=-2, color='r', linestyle='--', alpha=0.7)
        ax.axhline(y=0, color='g', linestyle='-', alpha=0.5, label='Mean')

        ax.set_title(f"Spread Analysis - {self.selected_pair_data['pair']}")
        ax.set_xlabel('Time')
        ax.set_ylabel('Z-Score')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Embed chart in tkinter
        canvas = FigureCanvasTkAgg(fig, self.pair_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    def toggle_monitoring(self):
        """Toggle real-time monitoring"""
        if not self.is_monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.viable_pairs:
            messagebox.showwarning("Warning", "No viable pairs found. Please screen pairs first.")
            return

        self.is_monitoring = True
        self.monitor_button.configure(text="Stop Monitoring", style='Warning.TButton')
        self.update_status("Real-time monitoring started...")

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_worker)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_monitoring = False
        self.monitor_button.configure(text="Start Monitoring", style='TButton')
        self.update_status("Monitoring stopped")

    def monitoring_worker(self):
        """Worker function for real-time monitoring"""
        while self.is_monitoring:
            try:
                # Update data for all viable pairs
                for i, pair in enumerate(self.viable_pairs):
                    if not self.is_monitoring:
                        break

                    # Re-analyze pair with fresh data
                    updated_analysis = self.engine.analyze_pair(
                        pair['symbol1'], pair['symbol2'], period='5d')

                    if updated_analysis.get('cointegrated'):
                        self.viable_pairs[i] = updated_analysis

                # Update GUI
                self.root.after(0, self.update_pairs_display)
                self.root.after(0, self.check_for_signals)

                # Wait before next update
                time.sleep(self.trading_config.DATA_REFRESH_MINUTES * 60)

            except Exception as e:
                self.log_queue.put(f"Monitoring error: {str(e)}")
                time.sleep(60)  # Wait longer on error

    def check_for_signals(self):
        """Check for new trading signals"""
        new_signals = []

        for pair in self.viable_pairs:
            signal = pair['current_signal']
            if signal['signal'] in ['LONG_PAIR', 'SHORT_PAIR'] and signal['strength'] >= 1.5:
                new_signals.append({
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'pair': pair['pair'],
                    'signal': signal['signal'],
                    'z_score': f"{pair['current_z_score']:.2f}",
                    'action': signal['action'],
                    'confidence': f"{signal['strength']:.1f}"
                })

        # Update signals tree
        if new_signals:
            # Clear old signals (keep last 20)
            children = self.signals_tree.get_children()
            if len(children) > 20:
                for child in children[:-20]:
                    self.signals_tree.delete(child)

            # Add new signals
            for signal in new_signals:
                self.signals_tree.insert('', 0, values=(
                    signal['time'], signal['pair'], signal['signal'],
                    signal['z_score'], signal['action'], signal['confidence']
                ))

            # Log new signals
            for signal in new_signals:
                self.signal_log.insert(END, 
                    f"[{signal['time']}] {signal['pair']}: {signal['signal']} "
                    f"(Z={signal['z_score']}, Conf={signal['confidence']})\n")
                self.signal_log.see(END)

    def execute_signal(self):
        """Execute selected trading signal (placeholder)"""
        selection = self.signals_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a signal to execute.")
            return

        messagebox.showinfo("Info", "Signal execution would happen here.\n"
                                   "In production, this would place actual trades via Kite API.")

    def paper_trade(self):
        """Execute paper trade (simulation)"""
        selection = self.signals_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a signal for paper trading.")
            return

        item = self.signals_tree.item(selection[0])
        pair_name = item['values'][1]
        signal_type = item['values'][2]

        # Add to positions tree (paper trade)
        self.positions_tree.insert('', 'end', values=(
            pair_name, signal_type, datetime.now().strftime("%H:%M:%S"),
            "Market Price", "₹0.00", "Paper Trade", "Close"
        ))

        messagebox.showinfo("Success", f"Paper trade executed for {pair_name}")

    def calculate_position(self):
        """Calculate position sizes for selected signal"""
        selection = self.signals_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a signal to calculate position.")
            return

        item = self.signals_tree.item(selection[0])
        pair_name = item['values'][1]

        # Find pair data
        pair_data = None
        for pair in self.viable_pairs:
            if pair['pair'] == pair_name:
                pair_data = pair
                break

        if pair_data:
            # Show position calculation dialog
            self.show_position_dialog(pair_data)

    def show_position_dialog(self, pair_data):
        """Show position calculation dialog"""
        dialog = Toplevel(self.root)
        dialog.title(f"Position Calculator - {pair_data['pair']}")
        dialog.geometry("400x300")
        dialog.resizable(False, False)

        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()

        # Position info
        info_text = f"""
Pair: {pair_data['pair']}
Hedge Ratio: {pair_data['cointegration_details']['hedge_ratio']:.3f}
Current Z-Score: {pair_data['current_z_score']:.2f}
Signal: {pair_data['current_signal']['signal']}

Capital Allocation: ₹{self.pair_config.CAPITAL_PER_PAIR:,}
Max Position Size: {self.trading_config.MAX_POSITION_SIZE*100:.1f}%
"""

        info_label = Label(dialog, text=info_text, justify=LEFT, font=('Arial', 10))
        info_label.pack(pady=20, padx=20)

        # Buttons
        btn_frame = Frame(dialog)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Calculate", 
                  command=lambda: self.calculate_actual_position(pair_data, dialog)).pack(side=LEFT, padx=10)
        ttk.Button(btn_frame, text="Close", 
                  command=dialog.destroy).pack(side=LEFT, padx=10)

        # Center dialog on parent
        dialog.update_idletasks()
        x = (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{self.root.winfo_x() + x}+{self.root.winfo_y() + y}")

    def calculate_actual_position(self, pair_data, dialog):
        """Calculate and display actual position sizes"""
        # This would fetch current prices and calculate positions
        messagebox.showinfo("Position Calculated", 
                           "Position calculation complete.\n"
                           "Results would be displayed here with actual prices from API.")
        dialog.destroy()

    def load_sample_trade_data(self):
        """Load sample trade history data"""
        sample_trades = [
            ('09:30:15', 'RELIANCE.NS-ONGC.NS', 'LONG', '100+50', '₹1,505.50', '₹45.30', '+₹850.20', 'Closed'),
            ('10:15:32', 'HDFC.NS-KOTAK.NS', 'SHORT', '75+80', '₹1,642.30', '₹38.75', '-₹120.50', 'Closed'),
            ('11:45:18', 'TCS.NS-INFY.NS', 'LONG', '50+55', '₹4,150.00', '₹52.10', '+₹425.80', 'Open'),
        ]

        for trade in sample_trades:
            self.history_tree.insert('', 'end', values=trade)

    def refresh_data(self):
        """Refresh all data"""
        self.update_status("Refreshing data...")
        # Implement data refresh logic
        messagebox.showinfo("Info", "Data refresh functionality would update all pair data.")

    def refresh_trade_history(self):
        """Refresh trade history"""
        # Clear and reload
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.load_sample_trade_data()
        messagebox.showinfo("Success", "Trade history refreshed")

    def export_data(self):
        """Export current data to CSV"""
        if not self.viable_pairs:
            messagebox.showwarning("Warning", "No data to export. Please screen pairs first.")
            return

        try:
            # Create DataFrame and export
            export_data = []
            for pair in self.viable_pairs:
                export_data.append({
                    'Pair': pair['pair'],
                    'P_Value': pair['cointegration_details']['p_value'],
                    'Hedge_Ratio': pair['cointegration_details']['hedge_ratio'],
                    'Correlation': pair['correlation'],
                    'Current_Z_Score': pair['current_z_score'],
                    'Signal': pair['current_signal']['signal'],
                    'Signal_Strength': pair['current_signal']['strength']
                })

            df = pd.DataFrame(export_data)
            filename = f"pairs_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)

            messagebox.showinfo("Success", f"Data exported to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def export_trades(self):
        """Export trade history"""
        messagebox.showinfo("Info", "Trade export functionality would save trade history to CSV.")

    def save_settings(self):
        """Save current settings"""
        try:
            # Update config values (in production, would save to file)
            self.trading_config.Z_SCORE_ENTRY = self.settings_vars['z_score_entry'].get()
            self.trading_config.Z_SCORE_EXIT = self.settings_vars['z_score_exit'].get()
            # ... update other settings

            messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def reset_settings(self):
        """Reset settings to defaults"""
        self.settings_vars['z_score_entry'].set(2.0)
        self.settings_vars['z_score_exit'].set(0.5)
        self.settings_vars['stop_loss_multiplier'].set(2.5)
        self.settings_vars['min_profit_threshold'].set(0.1)
        self.settings_vars['max_position_size'].set(2.0)
        self.settings_vars['rolling_window'].set(20)

        messagebox.showinfo("Success", "Settings reset to defaults")

    def calculate_fees(self):
        """Calculate and display trading fees"""
        try:
            quantity = self.fee_vars['quantity'].get()
            buy_price = self.fee_vars['buy_price'].get()
            sell_price = self.fee_vars['sell_price'].get()

            result = self.fee_calculator.calculate_total_charges(
                quantity, buy_price, sell_price, "intraday", "NSE"
            )

            # Display results
            self.fee_result_text.delete(1.0, END)

            output = f"""Fee Calculation Results
{'='*40}
Trade Details:
  Quantity: {result['trade_details']['quantity']} shares
  Buy Price: ₹{result['trade_details']['buy_price']}
  Sell Price: ₹{result['trade_details']['sell_price']}
  Buy Value: ₹{result['trade_details']['buy_value']:,.2f}
  Sell Value: ₹{result['trade_details']['sell_value']:,.2f}

Charges Breakdown:
  Brokerage: ₹{result['breakdown']['brokerage']}
  STT: ₹{result['breakdown']['stt']}
  Transaction Charges: ₹{result['breakdown']['transaction_charges']}
  SEBI Charges: ₹{result['breakdown']['sebi_charges']}
  Stamp Duty: ₹{result['breakdown']['stamp_duty']}
  GST: ₹{result['breakdown']['gst']}

Summary:
  Total Charges: ₹{result['totals']['total_charges']}
  Gross Profit: ₹{result['totals']['gross_profit']}
  Net Profit: ₹{result['totals']['net_profit']}
  Net Profit %: {result['totals']['net_profit_percent']}%
"""

            self.fee_result_text.insert(1.0, output)

        except Exception as e:
            messagebox.showerror("Error", f"Fee calculation failed: {str(e)}")

    def update_status(self, message):
        """Update status bar message"""
        self.status_label.configure(text=message)
        self.log_queue.put(message)

    def update_clock(self):
        """Update real-time clock"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.configure(text=current_time)
        self.root.after(1000, self.update_clock)

def main():
    """Main function to run the application"""
    root = tkinter.Tk()

    # Configure style
    style = ttk.Style()
    style.theme_use('clam')  # Use a modern theme

    # Configure custom styles
    style.configure('Accent.TButton', foreground='white')
    style.map('Accent.TButton', background=[('active', '#0078d4')])

    style.configure('Warning.TButton', foreground='white')
    style.map('Warning.TButton', background=[('active', '#d83b01')])

    # Create and run application
    app = StatisticalArbitrageDashboard(root)

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()