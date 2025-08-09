from ta.trend import EMAIndicator
from .base_signal_generator import BaseSignalGenerator

class EMACrossoverSignalGenerator(BaseSignalGenerator):
    def __init__(self, short_window=9, long_window=30):
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signal(self, df):
        """Generate signal based on EMA crossover"""
        df = df.copy()
        df['ema_short'] = EMAIndicator(close=df['close'], window=self.short_window).ema_indicator()
        df['ema_long'] = EMAIndicator(close=df['close'], window=self.long_window).ema_indicator()
        df = df.dropna()
        
        if len(df) < 2:
            return None
            
        latest = df.iloc[-1]
        previous = df.iloc[-2]

        if previous['ema_short'] < previous['ema_long'] and latest['ema_short'] > latest['ema_long']:
            return "buy"
        elif previous['ema_short'] > previous['ema_long'] and latest['ema_short'] < latest['ema_long']:
            return "sell"
        return None