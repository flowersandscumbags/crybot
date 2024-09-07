import os
import backtrader as bt
import pandas as pd
from datetime import datetime
from finnhub import Client as FinnhubClient
from dotenv import load_dotenv
import csv
import time
import schedule
from pathlib import Path

# Load environment variables
load_dotenv()
API_KEY = os.getenv('FINNHUB_API_KEY')
SYMBOLS = os.getenv('SYMBOLS').split(',')
MODE = os.getenv('MODE')
CSV_PATH = os.getenv('CSV_PATH')

# Initialize Finnhub Client
finnhub_client = FinnhubClient(api_key=API_KEY)

class CryptoStrategy(bt.Strategy):
    params = (
        ('tsi_period', 5),
        ('macd_signal_ema', 3),
        ('atr_period', 14),
        ('risk_limit', 0.50),
        ('trailing_stop_pct', 0.10),
        ('trading_fee', 0.001),  # Set fee to 0.1% (0.001 in decimal form)
    )

    def __init__(self):
        self.tsi = bt.ind.TSI(period=self.params.tsi_period)
        self.macd = bt.ind.MACD(signalperiod=self.params.macd_signal_ema)
        self.atr = bt.ind.ATR(period=self.params.atr_period)
        self.entry_price = None
        self.stop_loss_price = None

    def next(self):
        # Adjust trailing stop based on volatility (ATR)
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
                    # Apply trading fee when buying
                    size = size * (1 - self.params.trading_fee) 
                    self.buy(size=size)
                    self.entry_price = self.data.close[0]
                    self.stop_loss_price = self.data.close[0] * (1 - self.params.trading_fee) * (1 - self.params.trailing_stop_pct)

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
        return None  # Implement live data fetching here

def run_bot():
    cerebro = bt.Cerebro()
    cerebro.addstrategy(CryptoStrategy)

    for symbol in SYMBOLS:
        data = fetch_historical_data(symbol)
        if data is not None:
            data_feed = bt.feeds.PandasData(dataname=data)
            cerebro.adddata(data_feed)

    cerebro.broker.setcash(1000)
    cerebro.run()

# Append to CSV function
def append_to_csv(data, csv_file_path):
    try:
        with open(csv_file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)
    except PermissionError:
        print(f"Error: The file {csv_file_path} is open. Please close it and try again.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Retry API calls
def fetch_data_with_retries(api_call_function, retries=3):
    for i in range(retries):
        try:
            data = api_call_function()
            return data
        except Exception as e:
            print(f"API Error: {e}. Retrying... ({i+1}/{retries})")
            time.sleep(5)
    print("Max retries reached. Exiting.")
    return None

# Example: Append data every hour
schedule.every().hour.do(append_to_csv, data=['timestamp', 'price', 'volume'], csv_file_path=CSV_PATH)

while True:
    schedule.run_pending()
    time.sleep(1)

if __name__ == '__main__':
    run_bot()
