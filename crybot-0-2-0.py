import os
import backtrader as bt
import pandas as pd
from datetime import datetime
from finnhub import Client as FinnhubClient
from dotenv import load_dotenv
import csv
import time
import websocket
import json
from pathlib import Path

# Load environment variables
load_dotenv()
API_KEY = os.getenv('FINNHUB_API_KEY')
SYMBOLS = os.getenv('SYMBOLS').split(',')
MODE = os.getenv('MODE')  # Either 'HISTORICAL' or 'LIVE'
CSV_PATH = os.getenv('CSV_PATH')

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
        ('tsi_rperiod', 25),  # Relative period for TSI
        ('tsi_speriod', 13),  # Signal period for TSI
        ('macd_signal_ema', 9),
        ('atr_period', 14),
        ('risk_limit', 0.50),
        ('trailing_stop_pct', 0.10),
    )

    def __init__(self):
        # Corrected TSI indicator with the proper arguments
        self.tsi = bt.ind.TSI(rperiod=self.params.tsi_rperiod, speriod=self.params.tsi_speriod)
        self.macd = bt.ind.MACD(signalperiod=self.params.macd_signal_ema)
        self.atr = bt.ind.ATR(period=self.params.atr_period)
        self.entry_price = None

    def next(self):
        pass  # Placeholder for actual trading logic

    def make_initial_trade(self, price):
        # Make a sample buy trade at the start
        size = 1  # Fixed size for demo
        self.log_trade('BUY', price, size)

    def log_trade(self, action, price, quantity):
        with open(CSV_PATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now(), SYMBOLS[0], action, price, quantity])
        print(f"{action} {quantity} BTC at price: {price}")

# WebSocket Functions (placed outside the strategy class)
def on_message(ws, message):
    message = json.loads(message)
    
    # Check if the message is a custom ping
    if message.get('type') == 'ping':
        # Respond with a custom pong
        ws.send(json.dumps({'type': 'pong'}))
        print("Sent pong in response to ping")
    elif 'data' in message:
        # Handle the live data message
        for data in message['data']:
            price = data['p']
            symbol = data['s']
            print(f"Received new price for {symbol}: {price}")
            
            # Example strategy logic
            strategy = CryptoStrategy()
            strategy.make_initial_trade(price)

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def on_open(ws):
    print("WebSocket connection opened")
    # Subscribe to the symbols
    for symbol in SYMBOLS:
        ws.send(json.dumps({'type': 'subscribe', 'symbol': symbol}))

# WebSocket Initialization
def start_websocket():
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={API_KEY}",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

if __name__ == '__main__':
    if MODE == 'LIVE':
        start_websocket()  # Start WebSocket for live trading
    else:
        print("Running in historical mode...")  # Placeholder for historical mode
