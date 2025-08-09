import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ta.trend import EMAIndicator
import mplfinance as mpf
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import matplotlib.pyplot as plt
import os

# API credentials (reuse from main.py or set here)
API_KEY = "PKOY1TWMV7M28C48WW77"
API_SECRET = "91gfe8n8I194fISv9bHWblDTafSWjPmYxWctIjhe"

# Alpaca client
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

symbol = "SPY"
ema_short = 9
ema_long = 21
order_size = 5

def fetch_historical_data():
    end = datetime.now()
    start = end - timedelta(days=365)
    request = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Minute,
        start=start,
        end=end
    )
    bars = data_client.get_stock_bars(request).df
    if bars.empty:
        raise Exception(f"No data returned for {symbol}")
    if 'symbol' in bars.columns:
        df = bars[bars['symbol'] == symbol].copy()
    else:
        df = bars.copy()
    return df

def run_backtest(df):
    df['ema9'] = EMAIndicator(close=df['close'], window=ema_short).ema_indicator()
    df['ema21'] = EMAIndicator(close=df['close'], window=ema_long).ema_indicator()
    df = df.dropna()
    position = None
    entry_price = 0
    trades = []
    equity = 0
    equity_curve = []
    equity_time = []
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
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
        equity_curve.append(equity)
        equity_time.append(row.name)
    if position == "long":
        exit_price = df.iloc[-1]['close']
        trades.append({'type': 'sell', 'price': exit_price, 'time': df.iloc[-1].name})
        profit = (exit_price - entry_price) * order_size
        equity += profit
    # Pad equity curve to full df length
    while len(equity_curve) < len(df):
        equity_curve.append(equity)
        equity_time.append(df.index[len(equity_curve)-1])
    df['equity'] = equity_curve
    return df, trades, equity

def plot_trades(df, trades):
    # Ensure index is DatetimeIndex for resampling
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index(level=0, drop=True)
    # Resample to hourly for plotting
    df_plot = df.resample('1H').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'ema9': 'last',
        'ema21': 'last',
        'equity': 'last'
    })
    df_plot = df_plot.dropna()

    # Get period for labeling and filename
    start_str = df_plot.index.min().strftime('%Y-%m-%d')
    end_str = df_plot.index.max().strftime('%Y-%m-%d')
    interval = 'hourly'
    title = f"SPY Price, EMA Crossovers, Buy/Sell Signals ({interval.capitalize()}, {start_str} to {end_str})"
    filename = f"backtest_chart_{interval}_{start_str}_to_{end_str}.png"

    print(f"Plotting DataFrame shape: {df_plot.shape}, index type: {type(df_plot.index)}")
    print(f"First timestamp: {df_plot.index.min()}, Last timestamp: {df_plot.index.max()}")

    # --- Plot price/EMA/trade chart only ---
    fig = mpf.figure(style='yahoo', figsize=(18, 8))
    ax1 = fig.add_subplot(1,1,1)

    # Prepare overlays and markers after ax1 is defined
    apds = [
        mpf.make_addplot(df_plot['ema9'], color='blue', width=1.0, label='EMA9', ax=ax1),
        mpf.make_addplot(df_plot['ema21'], color='red', width=1.0, label='EMA21', ax=ax1),
    ]
    buy_signals = [t for t in trades if t['type'] == 'buy']
    sell_signals = [t for t in trades if t['type'] == 'sell']
    buy_idx = [t['time'] for t in buy_signals]
    buy_price = [t['price'] for t in buy_signals]
    sell_idx = [t['time'] for t in sell_signals]
    sell_price = [t['price'] for t in sell_signals]
    buy_marker = pd.Series(np.nan, index=df_plot.index)
    sell_marker = pd.Series(np.nan, index=df_plot.index)
    for idx, price in zip(buy_idx, buy_price):
        if isinstance(idx, pd.Timestamp):
            idx_hour = idx.floor('1H')
            if idx_hour in df_plot.index:
                buy_marker.loc[idx_hour] = price
    for idx, price in zip(sell_idx, sell_price):
        if isinstance(idx, pd.Timestamp):
            idx_hour = idx.floor('1H')
            if idx_hour in df_plot.index:
                sell_marker.loc[idx_hour] = price
    if not buy_marker.dropna().empty:
        apds.append(mpf.make_addplot(buy_marker, type='scatter', markersize=100, marker='^', color='green', label='Buy', ax=ax1))
    if not sell_marker.dropna().empty:
        apds.append(mpf.make_addplot(sell_marker, type='scatter', markersize=100, marker='v', color='red', label='Sell', ax=ax1))

    mpf.plot(
        df_plot,
        type='candle',
        addplot=apds,
        ax=ax1,
        xrotation=15,
        datetime_format='%Y-%m-%d %H:%M',
        warn_too_much_data=10000,
        tight_layout=True
    )
    ax1.set_title(title)
    ax1.set_ylabel('Price')
    plt.tight_layout()
    # Save the figure
    os.makedirs('assets', exist_ok=True)
    save_path = os.path.join('assets', filename)
    plt.savefig(save_path)
    print(f"Chart saved to {save_path}")
    plt.show()

def plot_equity_curve(df, save_path=None):
    # Fix index for plotting and resampling
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index(level=0, drop=True)
    # Resample to hourly for plotting
    df_plot = df.resample('1H').agg({'equity': 'last'})
    df_plot = df_plot.dropna()
    start_str = df_plot.index.min().strftime('%Y-%m-%d')
    end_str = df_plot.index.max().strftime('%Y-%m-%d')
    interval = 'hourly'
    title = f'Backtest Equity Curve ({interval.capitalize()}, {start_str} to {end_str})'
    if save_path is None:
        filename = f"equity_curve_{interval}_{start_str}_to_{end_str}.png"
        save_path = os.path.join('assets', filename)
    plt.figure(figsize=(16, 6))
    plt.plot(df_plot.index, df_plot['equity'], color='orange', linewidth=2, label='Equity Curve')
    plt.title(title)
    plt.xlabel('Time')
    plt.ylabel('Equity ($)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    print(f'Equity curve saved to {save_path}')
    plt.show()

if __name__ == "__main__":
    print("Fetching historical data...")
    df = fetch_historical_data()
    print("Running backtest...")
    df, trades, equity = run_backtest(df)
    print(f"Backtest complete! Total P/L: ${equity:.2f} | Trades: {len(trades)//2}")
    print("Plotting results (last 5 days)...")
    plot_trades(df, trades)
    plot_equity_curve(df) 