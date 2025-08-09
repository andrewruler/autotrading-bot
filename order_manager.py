from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
from config import config
import time

class OrderManager:
    def __init__(self):
        self.client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_API_SECRET, paper=True)
    
    def submit_order(self, side):
        """Submit a market order"""
        order = MarketOrderRequest(
            symbol=config.SYMBOL,
            qty=config.ORDER_SIZE,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.GTC
        )
        response = self.client.submit_order(order)
        print(f"✅ {side.upper()} order placed:", response)
        return response.id
    
    def check_order_status(self, order_id):
        """Check the status of an order"""
        try:
            order = self.client.get_order_by_id(order_id)
            print(f"Order {order_id} status: {order.status}")
            return order
        except Exception as e:
            print(f"⚠️ Error fetching order status: {e}")
            return None
    
    def cancel_order(self, order_id):
        """Cancel an open order"""
        try:
            self.client.cancel_order_by_id(order_id)
            print(f"❌ Order {order_id} canceled.")
        except Exception as e:
            print(f"⚠️ Error canceling order: {e}")
    
    def check_for_timeout(self, order_id, submitted_at):
        """Check if order has timed out"""
        if submitted_at and (time.time() - submitted_at > config.ORDER_TIMEOUT):
            print(f"Order {order_id} timed out. Canceling...")
            self.cancel_order(order_id)
            return True
        return False