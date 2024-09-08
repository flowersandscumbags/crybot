
import os
import backtrader as bt
import pandas as pd
from datetime import datetime
from finnhub import Client as FinnhubClient
from dotenv import load_dotenv
import csv
import time
from pathlib import Path
import schedule  # For better scheduled execution instead of while True

# Load environment variables
load_dotenv()
API_KEY = os.getenv('FINNHUB_API_KEY')
SYMBOLS = os.getenv('SYMBOLS').split(',')
MODE = os.getenv('MODE')  # Either 'HISTORICAL' or 'LIVE'
CSV_PATH = os.getenv('CSV_PATH')  # CSV file path from .env

# Initialize Finnhub Client
finnhub_client = FinnhubClient(api_key=API_KEY)

# Check if CSV exists, and if not, create it with headers
if not Path(CSV_PATH).is_file():
    print(f"File {CSV_PATH} not found. Creating a new file.")
    with open(CSV_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Symbol', 'Action', 'Price', 'Quantity'])  # Headers for CSV

# Define the strategy class
class CryptoStrategy(bt.Strategy):
    params = (
        ('tsi_period', 5),
        ('macd_signal_ema', 3),
        ('atr_period', 14),
        ('risk_limit', 0.50),
        ('trailing_stop_pct', 0.10),
    )

    def __init__(self):
        self.tsi = bt.ind.TSI(period=self.params.tsi_period)
        self.macd = bt.ind.MACD(signalperiod=self.params.macd_signal_ema)
        self.atr = bt.ind.ATR(period=self.params.atr_period)
        self.entry_price = None

    def next(self):
        pass  # Placeholder for actual trading logic

    def make_initial_trade(self):
        # Make a sample buy trade at the start
        initial_price = 54000  # Placeholder price
        size = 1  # Fixed size for demo
        self.log_trade('BUY', initial_price, size)

    def log_trade(self, action, price, quantity):
        with open(CSV_PATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now(), SYMBOLS[0], action, price, quantity])
        print(f"{action} {quantity} BTC at price: {price}")

# Refactored efficient loop using `schedule` for periodic execution
def run_strategy():
    print("Running the strategy...")
    # Initialize strategy and make the initial trade
    strategy = CryptoStrategy()
    strategy.make_initial_trade()

    # Simulate running the strategy and logging trade actions every 1 hour
    print("Fetching data and running strategy...")  # Placeholder for actual data fetch

# Schedule the strategy to run every hour
schedule.every(1).hours.do(run_strategy)

def continuous_run():
    try:
        # Run initial strategy execution once
        run_strategy()

        # Keep running according to the schedule
        while True:
            schedule.run_pending()
            time.sleep(1)  # Sleep for a short period to avoid resource overuse

    except KeyboardInterrupt:
        print("\nBot stopped by user.")

# Run the continuous loop
if __name__ == '__main__':
    continuous_run()


# Saving the updated code back to a new file so the user can download and use it.
with open("/mnt/data/crybot_with_trade_and_efficiency.py", "w") as updated_file:
    updated_file.write(updated_code_with_trade_and_efficiency)

# Return the path to the new file
"/mnt/data/crybot_with_trade_and_efficiency.py"
