# Crypto Paper Trading Bot
Crypto Micro Trade Strategy
The Crypto Micro Trade Strategy is designed for short-term trading with a focus on high volatility and momentum in cryptocurrency markets. It uses three key indicators to make informed buy/sell decisions:

TSI (True Strength Index): Detects momentum changes in price, with a 5-period setting for responsiveness.
MACD (Moving Average Convergence Divergence): Signals shifts in market trends, using a 3-period signal EMA for quicker detection of crossovers.
ATR (Average True Range): Measures volatility, helping to adjust stop losses dynamically based on market conditions.
Strategy Highlights:
Entry Conditions: Buy when TSI is positive, MACD shows a bullish crossover, and ATR indicates sufficient volatility.
Exit Conditions: Sell when MACD crosses below the signal line, TSI turns negative, or price drops below a dynamically set trailing stop based on ATR.
Risk Management: The strategy limits trades to a maximum of 50% of available capital and dynamically adjusts the trailing stop depending on market volatility.
Trailing Stop: The trailing stop loss starts at 10% but can adjust between 5%-20% based on market volatility.
Usage:
The strategy supports both historical backtesting and live trading (depending on the mode specified).
It operates with a single open position per symbol at a time, making sure no over-exposure occurs.

## Overview
This bot trades **BTC/USD**, **ETH/USD**, **LTC/USD**, and **DOGE/USD** using a strategy based on TSI, MACD, and ATR. 
It supports both live trading and historical backtesting using Finnhub API. There is a 1% trading fee calculated per buy/sell.

## Requirements
- Python 3.9+
- Finnhub API Key
- GITBash
## This bot uses the finnhub api. you can get a free key at finnhib.io
   

## Installation
1. Clone this repository. (
2. Create a .env file using notepad with the following info, replacing your api key, changing the symbols if you like, 
and historical or live.  

FINNHUB_API_KEY='your-api-key'
SYMBOLS='BTCUSD,ETHUSD,LTCUSD,DOGEUSD'
MODE='LIVE'  # Options: 'LIVE', 'HISTORICAL'
CSV_PATH='C:\\downloads\\backtest\\trades.csv'


3. Install dependencies:
   ```bash
   c$ "c:\users\<your user name>\crybot"
   
   pip install -r requirements.txt
   
## Run 
   $ Python crybot.py
