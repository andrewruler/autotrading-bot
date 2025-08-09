# Configuration for the trading system
class Config:
    # Alpaca credentials
    ALPACA_API_KEY = "PKEBJ18XJDALJ8X9ENZF"
    ALPACA_API_SECRET = "YgCkRRN5uhjbfwelNerDtIhxZ41GTJLzZgkMhlp2"
    
    # Trading parameters
    SYMBOL = "SPY"
    ORDER_SIZE = 30  # Shares per trade
    ORDER_TIMEOUT = 300  # seconds (5 minutes)
    
    # Data source configuration
    DATA_SOURCE = "alpaca"  # Options: "alpaca" or "yahoo"
    
    # Frequency configuration
    MAIN_LOOP_INTERVAL = 60  # seconds - how often to check for signals (default: 1 minute)
    ERROR_RETRY_INTERVAL = 300  # seconds - wait time after errors (default: 5 minutes)
    MARKET_CLOSED_INTERVAL = 60  # seconds - wait time when market is closed (default: 1 minute)
    
    # Data fetching intervals
    YAHOO_LIVE_INTERVAL = "1m"  # Yahoo Finance live data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    YAHOO_HISTORICAL_INTERVAL = "1d"  # Yahoo Finance historical data interval
    ALPACA_LIVE_INTERVAL = "1m"  # Alpaca live data interval
    ALPACA_HISTORICAL_INTERVAL = "1m"  # Alpaca historical data interval
    
    @property
    def HEADERS(self):
        return {
            "APCA-API-KEY-ID": self.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": self.ALPACA_API_SECRET
        }

# Create config instance
config = Config()