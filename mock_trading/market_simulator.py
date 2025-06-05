"""
Market simulator for mock trading environment
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .config import (
    SLIPPAGE_MODEL, COMMISSION_MODEL, DATA_CONFIG,
    START_DATE, END_DATE
)

class MarketSimulator:
    def __init__(self):
        self.current_time = START_DATE
        self.market_data = {}
        self.order_book = {}
        self.trades = []
        self._initialize_market_data()

    def _initialize_market_data(self):
        """Initialize market data for all symbols"""
        for symbol in DATA_CONFIG['symbols']:
            self.market_data[symbol] = self._generate_market_data(symbol)
            self.order_book[symbol] = self._initialize_order_book(symbol)

    def _generate_market_data(self, symbol):
        """Generate realistic market data with trends and volatility"""
        dates = pd.date_range(start=START_DATE, end=END_DATE, freq=DATA_CONFIG['timeframe'])
        n = len(dates)
        
        # Generate base price series with trend and volatility
        trend = np.random.normal(0.0001, 0.0002, n)  # Slight upward bias
        volatility = np.random.gamma(2, 0.0001, n)    # Realistic volatility
        returns = trend + volatility * np.random.normal(0, 1, n)
        prices = 100 * (1 + returns).cumprod()  # Start at $100
        
        # Generate other market data
        data = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.0001, n)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.0002, n))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.0002, n))),
            'close': prices,
            'volume': np.random.lognormal(10, 1, n),
            'vwap': prices * (1 + np.random.normal(0, 0.0001, n)),
            'bid': prices * (1 - np.random.normal(0, 0.0001, n)),
            'ask': prices * (1 + np.random.normal(0, 0.0001, n))
        }, index=dates)
        
        data['spread'] = data['ask'] - data['bid']
        return data

    def _initialize_order_book(self, symbol):
        """Initialize order book with realistic depth"""
        return {
            'bids': [(price, size) for price, size in zip(
                np.linspace(99, 100, 10),
                np.random.lognormal(5, 1, 10)
            )],
            'asks': [(price, size) for price, size in zip(
                np.linspace(100, 101, 10),
                np.random.lognormal(5, 1, 10)
            )]
        }

    def calculate_slippage(self, symbol, order_size, order_type):
        """Calculate realistic slippage based on order size and market conditions"""
        current_data = self.market_data[symbol].loc[self.current_time]
        base_slippage = SLIPPAGE_MODEL['base']
        volume_factor = SLIPPAGE_MODEL['volume_factor'] * (order_size / 100000)
        volatility_factor = SLIPPAGE_MODEL['volatility_factor'] * current_data['close'].pct_change().std()
        
        return base_slippage + volume_factor + volatility_factor

    def calculate_commission(self, order_value):
        """Calculate realistic commission based on order value"""
        commission = order_value * COMMISSION_MODEL['base']
        return max(
            min(commission, COMMISSION_MODEL['max_commission']),
            COMMISSION_MODEL['min_commission']
        )

    def execute_order(self, symbol, order_type, quantity, price=None):
        """Execute an order with realistic market impact"""
        if symbol not in self.market_data:
            raise ValueError(f"Symbol {symbol} not found in market data")
            
        current_data = self.market_data[symbol].loc[self.current_time]
        order_value = quantity * (price or current_data['close'])
        
        # Calculate slippage and commission
        slippage = self.calculate_slippage(symbol, order_value, order_type)
        commission = self.calculate_commission(order_value)
        
        # Execute the order
        execution_price = price or current_data['close']
        if order_type == 'MARKET':
            execution_price *= (1 + slippage if quantity > 0 else 1 - slippage)
            
        # Record the trade
        trade = {
            'timestamp': self.current_time,
            'symbol': symbol,
            'quantity': quantity,
            'price': execution_price,
            'commission': commission,
            'slippage': slippage * order_value
        }
        self.trades.append(trade)
        
        return trade

    def get_market_data(self, symbol, lookback=1):
        """Get historical market data for a symbol"""
        if symbol not in self.market_data:
            raise ValueError(f"Symbol {symbol} not found in market data")
            
        return self.market_data[symbol].loc[:self.current_time].tail(lookback)

    def advance_time(self, interval='1m'):
        """Advance the simulation time"""
        self.current_time += pd.Timedelta(interval)
        if self.current_time > END_DATE:
            raise StopIteration("Simulation period completed") 