import os
import backtrader as bt
import pandas as pd
from datetime import datetime
from finnhub import Client as FinnhubClient
from dotenv import load_dotenv
import csv
import time
from pathlib import Path

# Load environment variables
load_dotenv()
API_KEY = os.getenv('FINNHUB_API_KEY')
SYMBOLS = os.getenv('SYMBOLS').split(',')
MODE = os.getenv('MODE')  # Either 'HISTORICAL' or 'LIVE'
CSV_PATH = os.getenv('CSV_PATH')  # CSV file path from .env

# Initialize Finnhub Client
finnhub_client = FinnhubClient(api_key=API_KEY)

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
        self.stop_loss_price = None

    def next(self):
        self.adjust_trailing_stop()

        if self.position:
            if self.macd.macd < self.macd.signal or self.tsi < 0 or self.data.close[0] < self.stop_loss_price:
                self.sell()
            else:
                self.stop_loss_price = max(self.stop_loss_price, self.data.close[0] * (1 - self.params.trailing_stop_pct))
        else:
            if self.tsi[0] > 0 and self.macd.macd > self.macd.signal and self.atr[0] >= self.atr[-1]:
                size = self.calculate_position_size()
                if size > 0:
                    self.buy(size=size)
                    self.entry_price = self.data.close[0]
                    self.stop_loss_price = self.data.close[0] * (1 - self.params.trailing_stop_pct)

    def adjust_trailing_stop(self):
        atr_percent = self.atr[0] / self.data.close[0]
        if atr_percent < 0.01:
            self.params.trailing_stop_pct = 0.05
        elif atr_percent < 0.025:
            self.params.trailing_stop_pct = 0.10
        else:
            self.params.trailing_stop_pct = 0.20

    def calculate_position_size(self):
        available_cash = self.broker.getcash()
        return available_cash * self.params.risk_limit / self.data.close[0]

def fetch_historical_data(symbol):
    if MODE == 'HISTORICAL':
        res = finnhub_client.crypto_candles(symbol, 'D', int(datetime(2021, 1, 1).timestamp()), int(datetime.now().timestamp()))
        df = pd.DataFrame(res['candles'], columns=['t', 'o', 'h', 'l', 'c', 'v'])
        df['t'] = pd.to_datetime(df['t'], unit='s')
        return df[['t', 'o', 'h', 'l', 'c', 'v']].rename(columns={'t': 'datetime', 'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'})
    else:
        return None  # Live mode will be handled separately

def run_bot():
    cerebro = bt.Cerebro()
    cerebro.addstrategy(CryptoStrategy)

    # Add data feeds for each symbol
    for symbol in SYMBOLS:
        data = fetch_historical_data(symbol)
        if data is not None:
            data_feed = bt.feeds.PandasData(dataname=data)
            cerebro.adddata(data_feed)

    cerebro.broker.setcash(1000)
    cerebro.run()

# Function to append to CSV
def append_to_csv(data, csv_file_path):
    try:
        # Check if file exists, create headers if not
        file_exists = Path(csv_file_path).is_file()

        with open(csv_file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Timestamp', 'Price', 'Volume'])  # Header row
            writer.writerow(data)
    except PermissionError:
        print(f"Error: The file {csv_file_path} is open. Please close it and try again.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to fetch live data continuously and append to CSV
def fetch_live_data():
    iteration = 0
    while True:
        for symbol in SYMBOLS:
            try:
                print(f"Fetching live data for {symbol}...")  # Log live fetching
                # Add live data fetching logic here, e.g.:
                live_data = finnhub_client.quote(symbol)  # Fetch live price data
                timestamp = datetime.now()
                price = live_data['c']  # Closing price from live data
                volume = live_data['v']  # Volume from live data
                
                # Append to CSV
                append_to_csv([timestamp, price, volume], CSV_PATH)
                
                print(f"Data for {symbol} appended to CSV. Iteration {iteration}.")
                
                iteration += 1
                time.sleep(5)  # Wait 5 seconds before fetching again

            except Exception as e:
                print(f"Error fetching live data: {e}")
                time.sleep(5)  # Retry after short pause if error

if __name__ == '__main__':
    if MODE == 'HISTORICAL':
        run_bot()
    else:  # LIVE mode
        fetch_live_data()
