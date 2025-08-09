from abc import ABC, abstractmethod

class BaseSignalGenerator(ABC):
    @abstractmethod
    def generate_signal(self, df):
        """Generate trading signal from market data"""
        pass