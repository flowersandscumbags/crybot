import os
import backtrader as bt
import pandas as pd
from datetime import datetime
from finnhub import Client as FinnhubClient
from dotenv import load_dotenv
import csv
import time
import schedule
from websocket import create_connection
import json

# Load environment variables
load_dotenv()
API_KEY = os.getenv('FINNHUB_API_KEY')
SYMBOLS = os.getenv('SYMBOLS').split(',')
MODE = os.getenv('MODE')
CSV_PATH = os.getenv('CSV_PATH')

# Initialize Finnhub Client
finnhub_client = FinnhubClient(api_key=API_KEY)

# Define TSI Indicator
class TSI(bt.Indicator):
    lines = ('tsi',)
    params = (('r', 25), ('s', 13))

    def __init__(self):
        momentum = bt.indicators.MomentumOscillator(self.data, period=self.p.r)
        abs_momentum = bt.indicators.MomentumOscillator(self.data, period=self.p.r, movav=bt.indicators.MovAv.Exponential)
        self.tsi = bt.indicators.MovAv.Exponential(momentum, period=self.p.s) / bt.indicators.MovAv.Exponential(abs_momentum, period=self.p.s)

    def next(self):
        self.lines.tsi[0] = self.tsi[0]

# Define the Crypto Trading Strategy
class CryptoMicroTradeStrategy(bt.Strategy):
    params = (
        ('tsi_period', 5),
        ('macd_signal_ema', 3),
        ('atr_period', 14),
        ('risk_limit', 0.50),  # Max 50% of capital in use at any time
        ('trailing_stop_pct', 0.10),  # Default trailing stop (10%)
        ('trade_fee', 0.001)  # 0.1% trade fee
    )

    def __init__(self):
        # Initialize indicators
        self.tsi = TSI(period=self.params.tsi_period)
        self.macd = bt.ind.MACD(signalperiod=self.params.macd_signal_ema)
        self.atr = bt.ind.ATR(period=self.params.atr_period)
        self.entry_price = None
        self.stop_loss_price = None
        self.trailing_stop_pct = self.p.trailing_stop_pct

    def next(self):
        # Adjust trailing stop based on volatility (ATR)
        self.adjust_trailing_stop()

        if self.position:  # Already in trade
            if self.macd.macd < self.macd.signal or self.tsi < 0 or self.data.close[0] < self.stop_loss_price:
                self.sell()
            else:
                self.stop_loss_price = max(self.stop_loss_price, self.data.close[0] * (1 - self.trailing_stop_pct))
        else:  # Looking for entry
            if self.tsi[0] > 0 and self.macd.macd > self.macd.signal and self.atr[0] >= self.atr[-1]:
                size = self.calculate_position_size()
                if size > 0:
                    self.buy(size=size)
                    self.entry_price = self.data.close[0]
                    self.stop_loss_price = self.data.close[0] * (1 - self.trailing_stop_pct)

    def adjust_trailing_stop(self):
        atr_percent = self.atr[0] / self.data.close[0]
        if atr_percent < 0.01:
            self.trailing_stop_pct = 0.05
        elif atr_percent < 0.025:
            self.trailing_stop_pct = 0.10
        else:
            self.trailing_stop_pct = 0.20

    def calculate_position_size(self):
        available_cash = self.broker.getcash()
        size = available_cash * self.p.risk_limit / self.data.close[0]
        return size

# WebSocket to listen to real-time prices
def websocket_data(symbol):
    ws = create_connection(f"wss://ws.finnhub.io?token={API_KEY}")
    ws.send(json.dumps({'type': 'subscribe', 'symbol': symbol}))
    while True:
        result = ws.recv()
        print(result)
        time.sleep(1)  # Simulate fetching data
    ws.close()

# Fetch historical data
def fetch_historical_data(symbol):
    if MODE == 'HISTORICAL':
        res = finnhub_client.crypto_candles(symbol, 'D', int(datetime(2021, 1, 1).timestamp()), int(datetime.now().timestamp()))
        df = pd.DataFrame(res['candles'], columns=['t', 'o', 'h', 'l', 'c', 'v'])
        df['t'] = pd.to_datetime(df['t'], unit='s')
        return df[['t', 'o', 'h', 'l', 'c', 'v']].rename(columns={'t': 'datetime', 'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'})
    else:
        return None  # Use live WebSocket data for trading

# Run the bot with real-time data
def run_bot():
    cerebro = bt.Cerebro()
    cerebro.addstrategy(CryptoMicroTradeStrategy)

    # Add data feeds for each symbol
    for symbol in SYMBOLS:
        data = fetch_historical_data(symbol)
        if data is not None:
            data_feed = bt.feeds.PandasData(dataname=data)
            cerebro.adddata(data_feed)

    cerebro.broker.setcash(1000)
    cerebro.run()

# Append data to CSV
def append_to_csv(data, csv_file_path):
    try:
        with open(csv_file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)
    except PermissionError:
        print(f"Error: The file {csv_file_path} is open. Please close it and try again.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Handle API errors and retries
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

# Append every hour
schedule.every().hour.do(append_to_csv, data=['timestamp', 'price', 'volume'], csv_file_path=CSV_PATH)

if __name__ == '__main__':
    run_bot()
    while True:
        schedule.run_pending()
        time.sleep(1)
