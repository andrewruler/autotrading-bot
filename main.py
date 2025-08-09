from trading_engine import TradingEngine
from signal_generators.ema_crossover import EMACrossoverSignalGenerator
from config import config  # <-- Proper import
import sys
import time

def main():
    print("\n" + "="*50)
    print(f"🚀 Starting Trading System with {config.DATA_SOURCE.upper()} data")
    print("="*50 + "\n")
    
    signal_generator = EMACrossoverSignalGenerator(short_window=9, long_window=30)
    engine = TradingEngine(signal_generator, data_source=config.DATA_SOURCE)  # <-- Explicit source
    
    if config.DATA_SOURCE == "alpaca":
        if not engine.test_api_connection():
            print("❌ Cannot proceed without valid API connection")
            return
    
    if len(sys.argv) > 1 and sys.argv[1] == "backtest":
        engine.backtest()
        return
    
    print("🚀 Starting trading bot...")
    print(f"📊 Checking for signals every {config.MAIN_LOOP_INTERVAL} seconds...")
    while True:
        engine.run_iteration()
        time.sleep(config.MAIN_LOOP_INTERVAL)

if __name__ == "__main__":
    main()