import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ta.trend import EMAIndicator
import mplfinance as mpf
import matplotlib.pyplot as plt
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

API_KEY = "PKOY1TWMV7M28C48WW77"
API_SECRET = "91gfe8n8I194fISv9bHWblDTafSWjPmYxWctIjhe"
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
symbol = "SPY"
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

def run_backtest(df, ema_short, ema_long):
    df['ema_short'] = EMAIndicator(close=df['close'], window=ema_short).ema_indicator()
    df['ema_long'] = EMAIndicator(close=df['close'], window=ema_long).ema_indicator()
    df = df.dropna()
    position = None
    entry_price = 0
    trades = []
    equity = 0
    equity_curve = []
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        if prev['ema_short'] < prev['ema_long'] and row['ema_short'] > row['ema_long']:
            signal = "buy"
        elif prev['ema_short'] > prev['ema_long'] and row['ema_short'] < row['ema_long']:
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
    if position == "long":
        exit_price = df.iloc[-1]['close']
        trades.append({'type': 'sell', 'price': exit_price, 'time': df.iloc[-1].name})
        profit = (exit_price - entry_price) * order_size
        equity += profit
    # Pad equity curve to full df length
    while len(equity_curve) < len(df):
        equity_curve.append(equity)
    df['equity'] = equity_curve
    return df, trades, equity

def plot_results(df, trades, ema_short, ema_long):
    # Ensure index is DatetimeIndex for resampling
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index(level=0, drop=True)
    # Resample to hourly for plotting
    df_plot = df.resample('1H').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'ema_short': 'last',
        'ema_long': 'last',
        'equity': 'last'
    })
    df_plot = df_plot.dropna()
    start_str = df_plot.index.min().strftime('%Y-%m-%d')
    end_str = df_plot.index.max().strftime('%Y-%m-%d')
    interval = 'hourly'
    # Price/EMA/trade chart
    title = f"SPY Price, EMA{ema_short}/EMA{ema_long} Crossovers, Buy/Sell Signals ({interval.capitalize()}, {start_str} to {end_str})"
    filename = f"backtest_chart_ema{ema_short}_ema{ema_long}_{interval}_{start_str}_to_{end_str}.png"
    fig = mpf.figure(style='yahoo', figsize=(18, 8))
    ax1 = fig.add_subplot(1,1,1)
    apds = [
        mpf.make_addplot(df_plot['ema_short'], color='blue', width=1.0, label=f'EMA{ema_short}', ax=ax1),
        mpf.make_addplot(df_plot['ema_long'], color='red', width=1.0, label=f'EMA{ema_long}', ax=ax1),
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
    os.makedirs('assets', exist_ok=True)
    save_path = os.path.join('assets', filename)
    plt.savefig(save_path)
    print(f"Chart saved to {save_path}")
    plt.close(fig)
    # Equity curve
    eq_filename = f"equity_curve_ema{ema_short}_ema{ema_long}_{interval}_{start_str}_to_{end_str}.png"
    plt.figure(figsize=(16, 6))
    plt.plot(df_plot.index, df_plot['equity'], color='orange', linewidth=2, label='Equity Curve')
    plt.title(f'Backtest Equity Curve EMA{ema_short}/EMA{ema_long} ({interval.capitalize()}, {start_str} to {end_str})')
    plt.xlabel('Time')
    plt.ylabel('Equity ($)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    eq_save_path = os.path.join('assets', eq_filename)
    plt.savefig(eq_save_path)
    print(f'Equity curve saved to {eq_save_path}')
    plt.close()

def analyze_trades(trades):
    if not trades or len(trades) < 2:
        return {'num_trades': 0, 'win_rate': 0, 'max_drawdown': 0, 'best_trade': 0, 'worst_trade': 0, 'avg_trade': 0}
    profits = []
    equity = 0
    peak = 0
    max_dd = 0
    for i in range(0, len(trades)-1, 2):
        buy = trades[i]
        sell = trades[i+1]
        profit = sell['price'] - buy['price']
        profits.append(profit)
        equity += profit
        peak = max(peak, equity)
        dd = peak - equity
        max_dd = max(max_dd, dd)
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p <= 0]
    win_rate = len(wins) / len(profits) if profits else 0
    best_trade = max(profits) if profits else 0
    worst_trade = min(profits) if profits else 0
    avg_trade = np.mean(profits) if profits else 0
    return {
        'num_trades': len(profits),
        'win_rate': win_rate,
        'max_drawdown': max_dd,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'avg_trade': avg_trade
    }

def parameter_sweep():
    ema_short_list = [5, 9, 12]
    ema_long_list = [21, 30, 50]
    df = fetch_historical_data()
    results = []
    for ema_short in ema_short_list:
        for ema_long in ema_long_list:
            if ema_short >= ema_long:
                continue  # skip invalid combos
            print(f"\nRunning backtest for EMA{ema_short} / EMA{ema_long}...")
            df_bt, trades, equity = run_backtest(df.copy(), ema_short, ema_long)
            print(f"Total P/L: ${equity:.2f} | Trades: {len(trades)//2}")
            plot_results(df_bt, trades, ema_short, ema_long)
            stats = analyze_trades(trades)
            results.append({
                'ema_short': ema_short,
                'ema_long': ema_long,
                'total_pl': equity,
                'num_trades': stats['num_trades'],
                'win_rate': stats['win_rate'],
                'max_drawdown': stats['max_drawdown'],
                'best_trade': stats['best_trade'],
                'worst_trade': stats['worst_trade'],
                'avg_trade': stats['avg_trade']
            })
    # Write report
    report_lines = [
        "# EMA Parameter Sweep Backtest Report\n",
        f"Period: {df.index.min()} to {df.index.max()}\n",
        "| EMA Short | EMA Long | Total P/L | # Trades | Win Rate | Max Drawdown | Best Trade | Worst Trade | Avg Trade |",
        "|-----------|----------|-----------|----------|----------|--------------|------------|-------------|-----------|"
    ]
    for r in results:
        report_lines.append(
            f"| {r['ema_short']} | {r['ema_long']} | ${r['total_pl']:.2f} | {r['num_trades']} | {r['win_rate']*100:.1f}% | ${r['max_drawdown']:.2f} | ${r['best_trade']:.2f} | ${r['worst_trade']:.2f} | ${r['avg_trade']:.2f} |"
        )
    # Brief analysis
    best = max(results, key=lambda x: x['total_pl'])
    worst = min(results, key=lambda x: x['total_pl'])
    report_lines.append("\n## Analysis\n")
    report_lines.append(f"- Best result: EMA{best['ema_short']}/EMA{best['ema_long']} with total P/L ${best['total_pl']:.2f}")
    report_lines.append(f"- Worst result: EMA{worst['ema_short']}/EMA{worst['ema_long']} with total P/L ${worst['total_pl']:.2f}")
    report_lines.append("- Most robust settings have high win rate and low drawdown.")
    report = '\n'.join(report_lines)
    with open('sweep_report.md', 'w') as f:
        f.write(report)
    print("\nReport saved to sweep_report.md")

if __name__ == "__main__":
    parameter_sweep() 