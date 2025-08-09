from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderStatus
from config import config
from order_manager import OrderManager
import time
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log(message, color=Colors.END):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Colors.YELLOW}[{timestamp}]{color} {message}{Colors.END}")

class TradingEngine:
    def __init__(self, signal_generator, data_source=None):
        self.signal_generator = signal_generator
        self.data_source = data_source or config.DATA_SOURCE
        log(f"🔌 Using data source: {self.data_source.upper()}", Colors.CYAN)
        self._initialize_data_fetcher()
        self.order_manager = OrderManager()
        self.position = None
        self.open_order = {
            'id': None,
            'side': None,
            'submitted_at': None
        }
    
    def _initialize_data_fetcher(self):
        """Initialize the appropriate data fetcher based on configuration"""
        log(f"Initializing data fetcher for {self.data_source}...", Colors.BLUE)
        
        if self.data_source.lower() == "alpaca":
            from data_fetchers.alpaca_fetcher import AlpacaDataFetcher
            self.data_fetcher = AlpacaDataFetcher()
        elif self.data_source.lower() == "yahoo":
            from data_fetchers.yahoo_fetcher import YahooDataFetcher
            self.data_fetcher = YahooDataFetcher()
        else:
            raise ValueError(f"Unsupported data source: {self.data_source}")
        
        log(f"Data fetcher initialized: {self.data_fetcher.__class__.__name__}", Colors.GREEN)
    
    def test_api_connection(self):
        """Test if API credentials are working (Alpaca only)"""
        if self.data_source != "alpaca":
            log("Skipping API test for non-Alpaca data source", Colors.YELLOW)
            return True
            
        try:
            log("🔑 Attempting to connect to Alpaca API...", Colors.BLUE)
            account = self.order_manager.client.get_account()
            log("✅ API Connection successful!", Colors.GREEN)
            
            if not self.order_manager.client.get_clock().is_open:
                log("⏰ Market is closed. Sleeping...", Colors.YELLOW)
                time.sleep(config.MARKET_CLOSED_INTERVAL)
                
            log(f"Account ID: {account.id}", Colors.CYAN)
            log(f"Account Status: {account.status}", Colors.CYAN)
            log(f"Paper Trading: {account.pattern_day_trader}", Colors.CYAN)
            return True
        except Exception as e:
            log(f"❌ API Connection failed: {e}", Colors.RED)
            log(f"Error type: {type(e).__name__}", Colors.RED)
            log(f"Full error details: {str(e)}", Colors.RED)
            return False
    
    def handle_open_order(self):
        """Check and handle any open orders"""
        if not self.open_order['id']:
            return False
            
        order = self.order_manager.check_order_status(self.open_order['id'])
        if order:
            if order.status == OrderStatus.FILLED:
                if self.open_order['side'] == 'buy':
                    self.position = 'long'
                elif self.open_order['side'] == 'sell':
                    self.position = None
                log(f"Order {self.open_order['id']} filled. Position updated: {self.position}", Colors.GREEN)
                self.open_order = {'id': None, 'side': None, 'submitted_at': None}
                return True
            elif order.status in [OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.EXPIRED]:
                log(f"Order {self.open_order['id']} not filled (status: {order.status}). Resetting state.", Colors.YELLOW)
                self.open_order = {'id': None, 'side': None, 'submitted_at': None}
                return True
            else:
                if self.order_manager.check_for_timeout(self.open_order['id'], self.open_order['submitted_at']):
                    self.open_order = {'id': None, 'side': None, 'submitted_at': None}
                    return True
        return False
    
    def run_iteration(self):
        """Run one iteration of the trading loop"""
        try:
            # Handle any open orders first
            if self.handle_open_order():
                return
            
            # No open orders - check for new signals
            log("Fetching market data...", Colors.BLUE)
            df = self.data_fetcher.fetch_recent_data()
            trend = self.data_fetcher.get_trend(df)
            signal = self.signal_generator.generate_signal(df)
            log(f"📊 Trend: {trend} | 🪄 Signal: {signal} | 📈 Position: {self.position}", Colors.CYAN)

            if signal == "buy" and self.position is None:
                log("Generating BUY signal...", Colors.GREEN)
                order_id = self.order_manager.submit_order("buy")
                self.open_order = {'id': order_id, 'side': 'buy', 'submitted_at': time.time()}
                self.position = 'pending_buy'
            elif signal == "sell" and self.position == 'long':
                log("Generating SELL signal...", Colors.GREEN)
                order_id = self.order_manager.submit_order("sell")
                self.open_order = {'id': order_id, 'side': 'sell', 'submitted_at': time.time()}
                self.position = 'pending_sell'

        except Exception as e:
            log(f"⚠️ Error: {e}", Colors.RED)
            log(f"⏸️ Waiting {config.ERROR_RETRY_INTERVAL} seconds before retrying...", Colors.YELLOW)
            time.sleep(config.ERROR_RETRY_INTERVAL)
    
    def backtest(self, days=365):
        """Run a backtest with the current signal generator"""
        log(f"\n🔍 Starting BACKTEST with {self.data_source.upper()} data", Colors.BLUE)
        log(f"Using {self.signal_generator.__class__.__name__} strategy", Colors.CYAN)
        
        df = self.data_fetcher.fetch_historical_data(days)
        
        position = None
        entry_price = 0
        trades = []
        equity = 0

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Prepare the dataframe up to this point for signal generation
            current_df = df.iloc[:i+1].copy()
            signal = self.signal_generator.generate_signal(current_df)

            if signal == "buy" and position is None:
                position = "long"
                entry_price = row['close']
                trades.append({'type': 'buy', 'price': entry_price, 'time': row.name})
                log(f"BUY at {entry_price:.2f} on {row.name}", Colors.GREEN)
            elif signal == "sell" and position == "long":
                exit_price = row['close']
                trades.append({'type': 'sell', 'price': exit_price, 'time': row.name})
                profit = (exit_price - entry_price) * config.ORDER_SIZE
                equity += profit
                position = None
                log(f"SELL at {exit_price:.2f} on {row.name} (P/L: ${profit:.2f})", Colors.RED)

        # Close any open position at end
        if position == "long":
            exit_price = df.iloc[-1]['close']
            trades.append({'type': 'sell', 'price': exit_price, 'time': df.iloc[-1].name})
            profit = (exit_price - entry_price) * config.ORDER_SIZE
            equity += profit
            log(f"Closing position at {exit_price:.2f} (P/L: ${profit:.2f})", Colors.YELLOW)

        # Print summary
        num_trades = len(trades) // 2
        log("\nBacktest complete!", Colors.BLUE)
        log(f"Total trades: {num_trades}", Colors.CYAN)
        log(f"Total profit/loss: ${equity:.2f}", Colors.GREEN if equity >= 0 else Colors.RED)
        if num_trades > 0:
            log(f"Average profit/trade: ${equity/num_trades:.2f}", Colors.CYAN)
        else:
            log("No trades executed.", Colors.YELLOW)
        
        return trades