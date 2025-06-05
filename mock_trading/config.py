"""
Configuration for mock trading environment
"""
from datetime import datetime, timedelta

# Mock Trading Period
START_DATE = datetime.now() - timedelta(days=30)
END_DATE = datetime.now()

# Trading Parameters
INITIAL_CAPITAL = 1000000  # $1M initial capital
MAX_POSITION_SIZE = 0.1    # 10% of portfolio per position
MAX_LEVERAGE = 2.0         # Maximum leverage allowed
RISK_FREE_RATE = 0.02      # 2% risk-free rate for Sharpe ratio

# Market Simulation Parameters
SLIPPAGE_MODEL = {
    'base': 0.0001,        # Base slippage (0.01%)
    'volume_factor': 0.0002, # Additional slippage per $100k volume
    'volatility_factor': 0.0003 # Additional slippage per 1% volatility
}

COMMISSION_MODEL = {
    'base': 0.0001,        # Base commission (0.01%)
    'min_commission': 1.0,  # Minimum commission in USD
    'max_commission': 50.0  # Maximum commission in USD
}

# Risk Management
RISK_LIMITS = {
    'max_drawdown': 0.15,      # 15% maximum drawdown
    'max_daily_loss': 0.05,    # 5% maximum daily loss
    'max_position_risk': 0.02, # 2% maximum risk per position
    'max_correlation': 0.7     # Maximum correlation between positions
}

# Performance Metrics
METRICS = {
    'sharpe_ratio_window': 252,  # Trading days for Sharpe ratio
    'sortino_ratio_window': 252, # Trading days for Sortino ratio
    'max_drawdown_window': 252   # Trading days for max drawdown
}

# Data Parameters
DATA_CONFIG = {
    'timeframe': '1m',          # 1-minute data
    'symbols': [                # Trading symbols
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'TSLA', 'NVDA', 'AMD', 'INTC', 'CRM'
    ],
    'features': [               # Market data features
        'open', 'high', 'low', 'close', 'volume',
        'vwap', 'bid', 'ask', 'spread'
    ]
}

# Logging Configuration
LOGGING = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'mock_trading/logs/mock_trading.log'
} 