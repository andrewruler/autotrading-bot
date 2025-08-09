#!/usr/bin/env python3
"""
Frequency Configuration Examples

This file shows how to easily adjust the trading system frequencies
by modifying the config.py file.
"""

from config import config

def print_current_frequencies():
    """Print the current frequency settings"""
    print("🔧 Current Frequency Settings:")
    print("=" * 50)
    print(f"Main Loop Interval: {config.MAIN_LOOP_INTERVAL} seconds")
    print(f"Error Retry Interval: {config.ERROR_RETRY_INTERVAL} seconds")
    print(f"Market Closed Interval: {config.MARKET_CLOSED_INTERVAL} seconds")
    print(f"Yahoo Live Interval: {config.YAHOO_LIVE_INTERVAL}")
    print(f"Yahoo Historical Interval: {config.YAHOO_HISTORICAL_INTERVAL}")
    print(f"Alpaca Live Interval: {config.ALPACA_LIVE_INTERVAL}")
    print(f"Alpaca Historical Interval: {config.ALPACA_HISTORICAL_INTERVAL}")
    print()

def show_frequency_examples():
    """Show examples of different frequency configurations"""
    print("📊 Frequency Configuration Examples:")
    print("=" * 50)
    
    examples = [
        {
            "name": "High-Frequency Trading (1 minute)",
            "main_loop": 60,
            "yahoo_live": "1m",
            "description": "Checks every minute, uses 1-minute data"
        },
        {
            "name": "Medium-Frequency Trading (5 minutes)",
            "main_loop": 300,
            "yahoo_live": "5m",
            "description": "Checks every 5 minutes, uses 5-minute data"
        },
        {
            "name": "Low-Frequency Trading (15 minutes)",
            "main_loop": 900,
            "yahoo_live": "15m",
            "description": "Checks every 15 minutes, uses 15-minute data"
        },
        {
            "name": "Daily Trading (once per day)",
            "main_loop": 86400,
            "yahoo_live": "1d",
            "description": "Checks once per day, uses daily data"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['name']}")
        print(f"   Main Loop: {example['main_loop']} seconds")
        print(f"   Data Interval: {example['yahoo_live']}")
        print(f"   Description: {example['description']}")
        print()

def show_how_to_change():
    """Show how to change frequencies"""
    print("🔧 How to Change Frequencies:")
    print("=" * 50)
    print("1. Open config.py")
    print("2. Modify the frequency settings:")
    print()
    print("   # For high-frequency trading (every 30 seconds):")
    print("   MAIN_LOOP_INTERVAL = 30")
    print("   YAHOO_LIVE_INTERVAL = '1m'")
    print()
    print("   # For medium-frequency trading (every 5 minutes):")
    print("   MAIN_LOOP_INTERVAL = 300")
    print("   YAHOO_LIVE_INTERVAL = '5m'")
    print()
    print("   # For daily trading:")
    print("   MAIN_LOOP_INTERVAL = 86400  # 24 hours")
    print("   YAHOO_LIVE_INTERVAL = '1d'")
    print()
    print("3. Save config.py and restart the trading bot")
    print()

if __name__ == "__main__":
    print_current_frequencies()
    show_frequency_examples()
    show_how_to_change()
