import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from ta.trend import EMAIndicator
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
import requests

# API credentials
API_KEY = "PKEBJ18XJDALJ8X9ENZF"
API_SECRET = "YgCkRRN5uhjbfwelNerDtIhxZ41GTJLzZgkMhlp2"

# Alpaca clients
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
trading_client = TradingClient(API_KEY, API_SECRET, paper=True)

# Parameters
symbol = "SPY"
ema_short = 9
ema_long = 21
order_size = 5  # For backtest, 5 shares per trade
position = None

# Track open order info
open_order = {
    'id': None,
    'side': None,
    'submitted_at': None
}
ORDER_TIMEOUT = 300  # seconds (5 minutes)

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

def test_api_connection():
    """Test if API credentials are working"""
    try:
        # Test account info
        print("🔑 Attempting to connect to Alpaca API...")
        account = trading_client.get_account()
        print(f"✅ API Connection successful!")
        print(f"Account ID: {account.id}")
        print(f"Account Status: {account.status}")
        print(f"Paper Trading: {account.pattern_day_trader}")
        return True
    except Exception as e:
        print(f"❌ API Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Full error details: {str(e)}")
        
        # Check for specific error types
        if "403" in str(e):
            print("🔒 403 Forbidden - This usually means:")
            print("   - Your API credentials are invalid")
            print("   - Your account is suspended")
            print("   - You don't have permission for this endpoint")
        elif "401" in str(e):
            print("🔑 401 Unauthorized - Invalid API key or secret")
        elif "404" in str(e):
            print("🔍 404 Not Found - Endpoint doesn't exist")
        elif "429" in str(e):
            print("⏱️ 429 Rate Limited - Too many API requests")
        
        return False

def fetch_data():
    end = datetime.now()
    start = end - timedelta(minutes=200)  # Ensure enough candles for EMA
    request = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Minute,
        start=start,
        end=end
    )
    try:
        bars = data_client.get_stock_bars(request).df
        print("Fetched bars DataFrame columns:", bars.columns)
        print("First few rows:\n", bars.head())
    except Exception as e:
        print(f"❌ Data fetch error: {e}")
        if "403" in str(e):
            print("🔒 403 Forbidden - Check your API credentials and account status")
        elif "401" in str(e):
            print("🔑 401 Unauthorized - Invalid API credentials")
        elif "429" in str(e):
            print("⏱️ 429 Rate Limited - Too many requests")
        raise

    if bars.empty:
        raise Exception(f"No data returned for {symbol}")

    # Try to adapt to the DataFrame structure
    if 'symbol' in bars.columns:
        df = bars[bars['symbol'] == symbol].copy()
    else:
        df = bars.copy()  # If only one symbol, just use the DataFrame as is

    df['ema9'] = EMAIndicator(close=df['close'], window=ema_short).ema_indicator()
    df['ema21'] = EMAIndicator(close=df['close'], window=ema_long).ema_indicator()

    return df.dropna()

def get_trend(df):
    recent = df['close'].iloc[-10:]
    slope = np.polyfit(range(len(recent)), recent, 1)[0]
    if slope > 0:
        return "📈 Uptrend"
    elif slope < 0:
        return "📉 Downtrend"
    return "➖ Sideways"

def signal_generator(df):
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    print(f"Prev EMA9: {previous['ema9']:.2f}, EMA21: {previous['ema21']:.2f}")
    print(f"Latest EMA9: {latest['ema9']:.2f}, EMA21: {latest['ema21']:.2f}")

    if previous['ema9'] < previous['ema21'] and latest['ema9'] > latest['ema21']:
        return "buy"
    elif previous['ema9'] > previous['ema21'] and latest['ema9'] < latest['ema21']:
        return "sell"
    return None

def submit_order(side):
    order = MarketOrderRequest(
        symbol=symbol,
        qty=30,
        side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.GTC
    )
    response = trading_client.submit_order(order)
    print(f"✅ {side.upper()} order placed:", response)
    return response.id  # Return order ID

def check_order_status(order_id):
    try:
        order = trading_client.get_order_by_id(order_id)
        print(f"Order {order_id} status: {order.status}")
        return order
    except Exception as e:
        print(f"⚠️ Error fetching order status: {e}")
        return None

def cancel_order(order_id):
    try:
        trading_client.cancel_order_by_id(order_id)
        print(f"❌ Order {order_id} canceled.")
    except Exception as e:
        print(f"⚠️ Error canceling order: {e}")

def fetch_historical_data():
    """Fetch 1 year of minute data for SPY from Alpaca."""
    end = datetime.now()
    start = end - timedelta(days=365)
    request = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Minute,
        start=start,
        end=end
    )
    try:
        bars = data_client.get_stock_bars(request).df
        if bars.empty:
            raise Exception(f"No data returned for {symbol}")
        if 'symbol' in bars.columns:
            df = bars[bars['symbol'] == symbol].copy()
        else:
            df = bars.copy()
        return df
    except Exception as e:
        print(f"❌ Historical data fetch error: {e}")
        raise

def backtest():
    print("\n🔍 Starting backtest for 1 year of SPY minute data...")
    df = fetch_historical_data()
    df['ema9'] = EMAIndicator(close=df['close'], window=ema_short).ema_indicator()
    df['ema21'] = EMAIndicator(close=df['close'], window=ema_long).ema_indicator()
    df = df.dropna()

    position = None
    entry_price = 0
    trades = []
    equity = 0

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        # Signal logic
        if prev['ema9'] < prev['ema21'] and row['ema9'] > row['ema21']:
            signal = "buy"
        elif prev['ema9'] > prev['ema21'] and row['ema9'] < row['ema21']:
            signal = "sell"
        else:
            signal = None

        if signal == "buy" and position is None:
            position = "long"
            entry_price = row['close']
            trades.append({'type': 'buy', 'price': entry_price, 'time': row.name})
        elif signal == "sell" and position == "long":
            exit_price = row['close']
            trades.append({'type': 'sell', 'price': exit_price, 'time': row.name})
            profit = (exit_price - entry_price) * order_size
            equity += profit
            position = None

    # If still in position at end, close it
    if position == "long":
        exit_price = df.iloc[-1]['close']
        trades.append({'type': 'sell', 'price': exit_price, 'time': df.iloc[-1].name})
        profit = (exit_price - entry_price) * order_size
        equity += profit

    # Print summary
    num_trades = len(trades) // 2
    print(f"\nBacktest complete!")
    print(f"Total trades: {num_trades}")
    print(f"Total profit/loss: ${equity:.2f}")
    if num_trades > 0:
        print(f"Average profit/trade: ${equity/num_trades:.2f}")
    else:
        print("No trades executed.")
    print(f"First trade: {trades[0] if trades else 'N/A'}")
    print(f"Last trade: {trades[-1] if trades else 'N/A'}")
    return trades

def main():
    global position, open_order
    print("🔍 Testing API connection...")
    if not test_api_connection():
        print("❌ Cannot proceed without valid API connection")
        return

    print("🚀 Starting trading bot...")
    while True:
        try:
            # --- Check open order status ---
            if open_order['id']:
                order = check_order_status(open_order['id'])
                if order:
                    if order.status == OrderStatus.FILLED:
                        if open_order['side'] == 'buy':
                            position = 'long'
                        elif open_order['side'] == 'sell':
                            position = None
                        print(f"Order {open_order['id']} filled. Position updated: {position}")
                        open_order = {'id': None, 'side': None, 'submitted_at': None}
                    elif order.status in [OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.EXPIRED]:
                        print(f"Order {open_order['id']} not filled (status: {order.status}). Resetting state.")
                        open_order = {'id': None, 'side': None, 'submitted_at': None}
                    else:
                        # Check for timeout
                        if open_order['submitted_at'] and (time.time() - open_order['submitted_at'] > ORDER_TIMEOUT):
                            print(f"Order {open_order['id']} timed out. Canceling...")
                            cancel_order(open_order['id'])
                            open_order = {'id': None, 'side': None, 'submitted_at': None}
                        else:
                            print(f"Order {open_order['id']} still pending. Waiting...")
                            time.sleep(30)
                            continue  # Wait for order to resolve before new signals
                else:
                    print("Could not fetch order status. Will retry.")
                    time.sleep(30)
                    continue

            # --- No open order: check for new signals ---
            df = fetch_data()
            trend = get_trend(df)
            signal = signal_generator(df)
            print(f"📊 Trend: {trend} | 🪄 Signal: {signal}")

            if signal == "buy" and position is None:
                order_id = submit_order("buy")
                open_order = {'id': order_id, 'side': 'buy', 'submitted_at': time.time()}
                position = 'pending_buy'
            elif signal == "sell" and position == "long":
                order_id = submit_order("sell")
                open_order = {'id': order_id, 'side': 'sell', 'submitted_at': time.time()}
                position = 'pending_sell'

        except Exception as e:
            print("⚠️ Error:", e)
            print("⏸️ Waiting 5 minutes before retrying...")
            time.sleep(300)  # Wait 5 minutes on error
            continue

        time.sleep(60)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "backtest":
        backtest()
    else:
        main()

# Replace with your actual keys
API_KEY = "PKMY27OBWM8E7VPL3WK8"
API_SECRET = "DuMJNpVSB8vWgCykYNfptOpeUvPr4GGusAyUYuwc"

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

# 1. Test account info endpoint
account_url = "https://paper-api.alpaca.markets/v2/account"
resp = requests.get(account_url, headers=HEADERS)
print("Account info status:", resp.status_code)
print("Account info response:", resp.text)

# 2. Test market data endpoint (bars)
bars_url = "https://data.alpaca.markets/v2/stocks/SPY/bars?timeframe=1Min&limit=5"
resp = requests.get(bars_url, headers=HEADERS)
print("Bars status:", resp.status_code)
print("Bars response:", resp.text)
