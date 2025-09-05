"""
Config module initialization
"""

from typing import Dict, Any
import os
import json

class Config:
    """Configuration manager"""
    
    def __init__(self):
        self._config = {
            'available_capital': float(os.getenv('AVAILABLE_CAPITAL', '75000')),
            'max_daily_loss': float(os.getenv('MAX_DAILY_LOSS', '-2000')),
            'max_position_size': float(os.getenv('MAX_POSITION_SIZE', '0.10')),
            'min_trade_value': float(os.getenv('MIN_TRADE_VALUE', '20000')),
            'max_signals_per_cycle': int(os.getenv('MAX_SIGNALS_PER_CYCLE', '5')),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self._config[key] = value

# Global config instance
config = Config()
