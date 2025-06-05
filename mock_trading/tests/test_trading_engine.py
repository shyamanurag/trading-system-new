"""
Test suite for trading engine
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..trading_engine import TradingEngine
from ..config import INITIAL_CAPITAL, RISK_FREE_RATE, RISK_LIMITS

class TestTradingEngine(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.engine = TradingEngine()
        
    def test_initial_state(self):
        """Test initial state of trading engine"""
        self.assertEqual(self.engine.initial_capital, INITIAL_CAPITAL)
        self.assertEqual(self.engine.current_capital, INITIAL_CAPITAL)
        self.assertEqual(len(self.engine.positions), 0)
        self.assertEqual(len(self.engine.trades), 0)
        
    def test_market_order(self):
        """Test market order execution"""
        # Test buy order
        trade = self.engine.execute_market_order(
            symbol="AAPL",
            quantity=100,
            timestamp=datetime.now()
        )
        
        self.assertIsNotNone(trade)
        self.assertEqual(trade['symbol'], "AAPL")
        self.assertEqual(trade['quantity'], 100)
        self.assertIn('price', trade)
        self.assertIn('commission', trade)
        self.assertIn('slippage', trade)
        
        # Test sell order
        trade = self.engine.execute_market_order(
            symbol="AAPL",
            quantity=-100,
            timestamp=datetime.now()
        )
        
        self.assertIsNotNone(trade)
        self.assertEqual(trade['symbol'], "AAPL")
        self.assertEqual(trade['quantity'], -100)
        self.assertIn('price', trade)
        self.assertIn('commission', trade)
        self.assertIn('slippage', trade)
        
    def test_limit_order(self):
        """Test limit order execution"""
        # Test buy order
        trade = self.engine.execute_limit_order(
            symbol="AAPL",
            quantity=100,
            price=150.00,
            timestamp=datetime.now()
        )
        
        self.assertIsNotNone(trade)
        self.assertEqual(trade['symbol'], "AAPL")
        self.assertEqual(trade['quantity'], 100)
        self.assertLessEqual(trade['price'], 150.00)
        self.assertIn('commission', trade)
        self.assertIn('slippage', trade)
        
        # Test sell order
        trade = self.engine.execute_limit_order(
            symbol="AAPL",
            quantity=-100,
            price=160.00,
            timestamp=datetime.now()
        )
        
        self.assertIsNotNone(trade)
        self.assertEqual(trade['symbol'], "AAPL")
        self.assertEqual(trade['quantity'], -100)
        self.assertGreaterEqual(trade['price'], 160.00)
        self.assertIn('commission', trade)
        self.assertIn('slippage', trade)
        
    def test_position_tracking(self):
        """Test position tracking"""
        # Test buy order
        self.engine.execute_market_order(
            symbol="AAPL",
            quantity=100,
            timestamp=datetime.now()
        )
        
        self.assertIn("AAPL", self.engine.positions)
        position = self.engine.positions["AAPL"]
        self.assertEqual(position['quantity'], 100)
        self.assertGreater(position['avg_price'], 0)
        
        # Test sell order
        self.engine.execute_market_order(
            symbol="AAPL",
            quantity=-50,
            timestamp=datetime.now()
        )
        
        position = self.engine.positions["AAPL"]
        self.assertEqual(position['quantity'], 50)
        
    def test_trade_recording(self):
        """Test trade recording"""
        # Execute trade
        trade = self.engine.execute_market_order(
            symbol="AAPL",
            quantity=100,
            timestamp=datetime.now()
        )
        
        self.assertEqual(len(self.engine.trades), 1)
        recorded_trade = self.engine.trades[0]
        self.assertEqual(recorded_trade['symbol'], trade['symbol'])
        self.assertEqual(recorded_trade['quantity'], trade['quantity'])
        self.assertEqual(recorded_trade['price'], trade['price'])
        
    def test_capital_tracking(self):
        """Test capital tracking"""
        initial_capital = self.engine.current_capital
        
        # Execute profitable trade
        self.engine.execute_market_order(
            symbol="AAPL",
            quantity=100,
            timestamp=datetime.now()
        )
        
        # Check capital decreased
        self.assertLess(self.engine.current_capital, initial_capital)
        
        # Execute losing trade
        self.engine.execute_market_order(
            symbol="AAPL",
            quantity=-100,
            timestamp=datetime.now()
        )
        
        # Check capital increased
        self.assertGreater(self.engine.current_capital, initial_capital)
        
    def test_risk_limits(self):
        """Test risk limit enforcement"""
        # Test within limits
        trade = self.engine.execute_market_order(
            symbol="AAPL",
            quantity=100,
            timestamp=datetime.now()
        )
        
        self.assertIsNotNone(trade)
        
        # Test exceeding limits
        trade = self.engine.execute_market_order(
            symbol="AAPL",
            quantity=1000000,
            timestamp=datetime.now()
        )
        
        self.assertIsNone(trade)
        
    def test_order_types(self):
        """Test different order types"""
        # Test market order
        market_trade = self.engine.execute_market_order(
            symbol="AAPL",
            quantity=100,
            timestamp=datetime.now()
        )
        
        self.assertIsNotNone(market_trade)
        
        # Test limit order
        limit_trade = self.engine.execute_limit_order(
            symbol="AAPL",
            quantity=100,
            price=150.00,
            timestamp=datetime.now()
        )
        
        self.assertIsNotNone(limit_trade)
        
    def test_multiple_symbols(self):
        """Test trading across multiple symbols"""
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        for symbol in symbols:
            # Execute buy order
            trade = self.engine.execute_market_order(
                symbol=symbol,
                quantity=100,
                timestamp=datetime.now()
            )
            
            self.assertIsNotNone(trade)
            self.assertEqual(trade['symbol'], symbol)
            self.assertEqual(trade['quantity'], 100)
            
            # Execute sell order
            trade = self.engine.execute_market_order(
                symbol=symbol,
                quantity=-100,
                timestamp=datetime.now()
            )
            
            self.assertIsNotNone(trade)
            self.assertEqual(trade['symbol'], symbol)
            self.assertEqual(trade['quantity'], -100)
            
    def test_trade_statistics(self):
        """Test trade statistics calculation"""
        # Execute series of trades
        trades = [
            {'symbol': 'AAPL', 'quantity': 100},  # Buy
            {'symbol': 'AAPL', 'quantity': -100}, # Sell
            {'symbol': 'MSFT', 'quantity': 100},  # Buy
            {'symbol': 'MSFT', 'quantity': -100}  # Sell
        ]
        
        for trade in trades:
            self.engine.execute_market_order(
                symbol=trade['symbol'],
                quantity=trade['quantity'],
                timestamp=datetime.now()
            )
            
        # Check statistics
        stats = self.engine.get_trade_statistics()
        self.assertEqual(stats['total_trades'], len(trades))
        self.assertGreaterEqual(stats['winning_trades'], 0)
        self.assertGreaterEqual(stats['losing_trades'], 0)
        self.assertGreaterEqual(stats['win_rate'], 0)
        self.assertLessEqual(stats['win_rate'], 1)

if __name__ == '__main__':
    unittest.main() 