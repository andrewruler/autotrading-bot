from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data import TimeFrame
import pandas as pd
import numpy as np
from config import config

class AlpacaDataFetcher:
    def __init__(self):
        print("📡 Initializing Alpaca data connection...")
        self.client = StockHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_API_SECRET)
    
    def fetch_recent_data(self, minutes=200):
        """Fetch recent market data for analysis"""
        print(f"📊 Fetching recent data from {self.__class__.__name__}...")
        
        end = datetime.now()
        start = end - timedelta(minutes=minutes)
        request = StockBarsRequest(
            symbol_or_symbols=[config.SYMBOL],
            timeframe=TimeFrame.Minute if config.ALPACA_LIVE_INTERVAL == "1m" else TimeFrame.Hour,
            start=start,
            end=end
        )
        bars = self.client.get_stock_bars(request).df
        
        if bars.empty:
            raise Exception(f"No data returned for {config.SYMBOL}")

        if 'symbol' in bars.columns:
            df = bars[bars['symbol'] == config.SYMBOL].copy()
        else:
            df = bars.copy()

        return df
    
    def fetch_historical_data(self, days=365):
        """Fetch historical data for backtesting"""
        end = datetime.now()
        start = end - timedelta(days=days)
        request = StockBarsRequest(
            symbol_or_symbols=[config.SYMBOL],
            timeframe=TimeFrame.Minute if config.ALPACA_HISTORICAL_INTERVAL == "1m" else TimeFrame.Hour,
            start=start,
            end=end
        )
        bars = self.client.get_stock_bars(request).df
        
        if bars.empty:
            raise Exception(f"No data returned for {config.SYMBOL}")

        if 'symbol' in bars.columns:
            df = bars[bars['symbol'] == config.SYMBOL].copy()
        else:
            df = bars.copy()

        return df
    
    def get_trend(self, df):
        """Determine the market trend"""
        recent = df['close'].iloc[-10:]
        slope = np.polyfit(range(len(recent)), recent, 1)[0]
        if slope > 0:
            return "📈 Uptrend"
        elif slope < 0:
            return "📉 Downtrend"
        return "➖ Sideways"