import os
import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from dotenv import load_dotenv
import csv
from pathlib import Path

# Load environment variables
load_dotenv()

# Define necessary environment variables
FINNHUB_SYMBOLS = os.getenv('FINNHUB_SYMBOLS')
YFINANCE_SYMBOLS = os.getenv('YFINANCE_SYMBOLS').split(',')
INTERVAL = os.getenv('INTERVAL', '1d')  # Default to 1-day interval
MODE = os.getenv('MODE')  # Either 'HISTORICAL' or 'LIVE'
CSV_PATH = os.getenv('CSV_PATH')

# Check if CSV exists, and if not, create it with headers
if not Path(CSV_PATH).is_file():
    print(f"File {CSV_PATH} not found. Creating a new file.")
    with open(CSV_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Symbol', 'Action', 'Price', 'Quantity', 'Spent/Received', 'Cum P/L'])  # Headers for CSV

class CryptoStrategy(bt.Strategy):
    params = (
        ('tsi_rperiod', 25),  
        ('tsi_speriod', 13),
        ('macd_signal_ema', 9),
        ('atr_period', 14),
        ('risk_limit', 0.50),
        ('trailing_stop_pct', 0.10),
    )

    def __init__(self):
        # Custom TSI indicator
        self.tsi = bt.ind.TSI(rperiod=self.params.tsi_rperiod, speriod=self.params.tsi_speriod)
        self.macd = bt.ind.MACD(signalperiod=self.params.macd_signal_ema)
        self.atr = bt.ind.ATR(period=self.params.atr_period)
        self.entry_price = None
        self.cum_pnl = 0  # Initialize cumulative profit/loss
        self.buy_price = 0  # To track the buy price

    def next(self):
        current_price = self.data.close[0]
        quantity = 0.1  # Example quantity
        
        # Buy logic
        if self.tsi[0] > 0 and self.macd.macd > self.macd.signal:  
            self.buy_price = current_price
            spent = self.buy_price * quantity
            self.log_trade('BUY', current_price, quantity, spent, self.data._name)  # Pass the symbol dynamically
            
        # Sell logic
        elif self.tsi[0] < 0 and self.macd.macd < self.macd.signal:
            received = current_price * quantity
            pnl = (received - self.buy_price * quantity)  # Calculate profit/loss
            self.cum_pnl += pnl  # Update cumulative P/L
            self.log_trade('SELL', current_price, quantity, received, self.data._name, pnl)  # Pass the symbol dynamically

    def log_trade(self, action, price, quantity, spent_received, symbol, pnl=None):
        timestamp = self.data.datetime.datetime(0)  # Proper timestamp
        with open(CSV_PATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            if action == 'SELL':
                writer.writerow([timestamp, symbol, action, price, quantity, spent_received, self.cum_pnl])
                print(f"Logged {action} action for {symbol} at {price} to CSV, Cum P/L: {self.cum_pnl}")
            else:
                writer.writerow([timestamp, symbol, action, price, quantity, spent_received, '-'])
                print(f"Logged {action} action for {symbol} at {price} to CSV")

# Backtesting function to fetch data and run the strategy
def run_historical_backtest():
    print("Running historical backtest...")

    # Create a Cerebro engine
    cerebro = bt.Cerebro()

    # Add the CryptoStrategy to Cerebro
    cerebro.addstrategy(CryptoStrategy)

    # Define the time range for the backtest
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # Backtest for 1 year

    for symbol in YFINANCE_SYMBOLS:
        try:
            print(f"Fetching historical data for {symbol} from {start_date} to {end_date} with {INTERVAL} interval")
            data = yf.download(symbol, start=start_date, end=end_date, interval=INTERVAL)

            if data.empty:
                print(f"Successfully ran but no data found for {symbol}")
                continue

            datafeed = bt.feeds.PandasData(dataname=data, name=symbol)  # Attach the symbol as the data feed name
            cerebro.adddata(datafeed)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
    
    # Run the backtest
    cerebro.run()

# Run the bot
if __name__ == '__main__':
    if MODE == 'LIVE':
        # Start WebSocket for live trading (already implemented in your previous code)
        pass
    else:
        run_historical_backtest()  # Run historical backtest
