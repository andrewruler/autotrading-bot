import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import config

class YahooDataFetcher:
    def __init__(self):
        print("📡 Initializing Yahoo Finance data connection...")
        self.ticker = yf.Ticker(config.SYMBOL)
    
    def fetch_recent_data(self, minutes=200):
        print(f"📊 Fetching recent data from {self.__class__.__name__}...")

        """Fetch recent market data for analysis from Yahoo Finance"""
        # Yahoo Finance minimum interval is 1m, but we need to adjust for their API limits
        period = "1d"  # Maximum period for 1m data is 7 days
        interval = config.YAHOO_LIVE_INTERVAL
        
        df = yf.download(
            tickers=config.SYMBOL,
            period=period,
            interval=interval,
            progress=False
        )
        
        if df.empty:
            raise Exception(f"No data returned for {config.SYMBOL}")
            
        return df
    
    def fetch_historical_data(self, days=365):
        """Fetch historical data for backtesting from Yahoo Finance"""
        # For historical data, we'll use daily data to avoid hitting API limits
        period = f"{days}d"
        interval = config.YAHOO_HISTORICAL_INTERVAL
        
        df = yf.download(
            tickers=config.SYMBOL,
            period=period,
            interval=interval,
            progress=False
        )
        
        if df.empty:
            raise Exception(f"No data returned for {config.SYMBOL}")
            
        return df
    
    def get_trend(self, df):
        """Determine the market trend"""
        recent = df['Close'].iloc[-10:] if 'Close' in df.columns else df['close'].iloc[-10:]
        slope = np.polyfit(range(len(recent)), recent, 1)[0]
        if slope > 0:
            return "📈 Uptrend"
        elif slope < 0:
            return "📉 Downtrend"
        return "➖ Sideways"