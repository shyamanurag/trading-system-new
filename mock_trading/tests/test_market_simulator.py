"""
Test suite for market simulator
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..market_simulator import MarketSimulator
from ..config import START_DATE, END_DATE, DATA_CONFIG

class TestMarketSimulator(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.market = MarketSimulator()
        
    def test_market_data_generation(self):
        """Test market data generation"""
        for symbol in DATA_CONFIG['symbols']:
            # Check if data exists
            self.assertIn(symbol, self.market.market_data)
            
            # Get data
            data = self.market.market_data[symbol]
            
            # Check data structure
            self.assertIsInstance(data, pd.DataFrame)
            self.assertTrue(all(col in data.columns for col in DATA_CONFIG['features']))
            
            # Check data range
            self.assertTrue(data.index.min() >= START_DATE)
            self.assertTrue(data.index.max() <= END_DATE)
            
            # Check data quality
            self.assertFalse(data.isnull().any().any())
            self.assertTrue(all(data['high'] >= data['low']))
            self.assertTrue(all(data['ask'] >= data['bid']))
            
    def test_order_book(self):
        """Test order book functionality"""
        for symbol in DATA_CONFIG['symbols']:
            # Check if order book exists
            self.assertIn(symbol, self.market.order_book)
            
            # Get order book
            book = self.market.order_book[symbol]
            
            # Check structure
            self.assertIn('bids', book)
            self.assertIn('asks', book)
            
            # Check price ordering
            bid_prices = [price for price, _ in book['bids']]
            ask_prices = [price for price, _ in book['asks']]
            self.assertTrue(all(bid_prices[i] >= bid_prices[i+1] for i in range(len(bid_prices)-1)))
            self.assertTrue(all(ask_prices[i] <= ask_prices[i+1] for i in range(len(ask_prices)-1)))
            
            # Check spread
            self.assertTrue(min(ask_prices) > max(bid_prices))
            
    def test_slippage_calculation(self):
        """Test slippage calculation"""
        symbol = DATA_CONFIG['symbols'][0]
        
        # Test small order
        small_slippage = self.market.calculate_slippage(symbol, 1000, 'MARKET')
        self.assertGreaterEqual(small_slippage, 0)
        
        # Test large order
        large_slippage = self.market.calculate_slippage(symbol, 1000000, 'MARKET')
        self.assertGreaterEqual(large_slippage, small_slippage)
        
    def test_commission_calculation(self):
        """Test commission calculation"""
        # Test minimum commission
        min_commission = self.market.calculate_commission(100)
        self.assertGreaterEqual(min_commission, 1.0)
        
        # Test maximum commission
        max_commission = self.market.calculate_commission(1000000)
        self.assertLessEqual(max_commission, 50.0)
        
        # Test proportional commission
        commission1 = self.market.calculate_commission(1000)
        commission2 = self.market.calculate_commission(2000)
        self.assertGreater(commission2, commission1)
        
    def test_order_execution(self):
        """Test order execution"""
        symbol = DATA_CONFIG['symbols'][0]
        
        # Test market order
        market_trade = self.market.execute_order(
            symbol=symbol,
            order_type='MARKET',
            quantity=100
        )
        self.assertIn('timestamp', market_trade)
        self.assertIn('price', market_trade)
        self.assertIn('quantity', market_trade)
        self.assertEqual(market_trade['quantity'], 100)
        
        # Test limit order
        limit_trade = self.market.execute_order(
            symbol=symbol,
            order_type='LIMIT',
            quantity=100,
            price=150.00
        )
        self.assertIn('timestamp', limit_trade)
        self.assertIn('price', limit_trade)
        self.assertIn('quantity', limit_trade)
        
    def test_market_data_access(self):
        """Test market data access methods"""
        symbol = DATA_CONFIG['symbols'][0]
        
        # Test get_market_data
        data = self.market.get_market_data(symbol)
        self.assertIsInstance(data, pd.DataFrame)
        self.assertTrue(len(data) > 0)
        
        # Test with lookback
        data = self.market.get_market_data(symbol, lookback=5)
        self.assertEqual(len(data), 5)
        
    def test_time_advancement(self):
        """Test time advancement"""
        initial_time = self.market.current_time
        
        # Advance time
        self.market.advance_time()
        self.assertGreater(self.market.current_time, initial_time)
        
        # Test end of simulation
        self.market.current_time = END_DATE
        with self.assertRaises(StopIteration):
            self.market.advance_time()
            
    def test_market_impact(self):
        """Test market impact of large orders"""
        symbol = DATA_CONFIG['symbols'][0]
        
        # Get initial price
        initial_data = self.market.get_market_data(symbol)
        initial_price = initial_data['close'].iloc[-1]
        
        # Execute large order
        self.market.execute_order(
            symbol=symbol,
            order_type='MARKET',
            quantity=1000000
        )
        
        # Check price impact
        new_data = self.market.get_market_data(symbol)
        new_price = new_data['close'].iloc[-1]
        self.assertNotEqual(initial_price, new_price)
        
    def test_data_consistency(self):
        """Test data consistency across time periods"""
        symbol = DATA_CONFIG['symbols'][0]
        
        # Get data for different time periods
        data1 = self.market.get_market_data(symbol, lookback=10)
        self.market.advance_time()
        data2 = self.market.get_market_data(symbol, lookback=10)
        
        # Check overlap
        overlap = pd.merge(data1, data2, how='inner', left_index=True, right_index=True)
        self.assertTrue(len(overlap) > 0)
        
        # Check consistency
        for col in DATA_CONFIG['features']:
            self.assertTrue(all(overlap[f'{col}_x'] == overlap[f'{col}_y']))

if __name__ == '__main__':
    unittest.main() 