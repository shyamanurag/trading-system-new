"""
Test suite for risk manager
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..risk_manager import RiskManager
from ..config import RISK_LIMITS, POSITION_LIMITS

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.risk_manager = RiskManager()
        
    def test_initial_state(self):
        """Test initial state of risk manager"""
        self.assertEqual(len(self.risk_manager.positions), 0)
        self.assertEqual(len(self.risk_manager.trades), 0)
        self.assertEqual(self.risk_manager.current_capital, 0)
        
    def test_position_limits(self):
        """Test position limit checking"""
        # Test within limits
        self.assertTrue(self.risk_manager.check_position_limits(
            symbol="AAPL",
            quantity=100,
            price=150.00
        ))
        
        # Test exceeding limits
        self.assertFalse(self.risk_manager.check_position_limits(
            symbol="AAPL",
            quantity=1000000,
            price=150.00
        ))
        
    def test_risk_limits(self):
        """Test risk limit checking"""
        # Test within limits
        self.assertTrue(self.risk_manager.check_risk_limits(
            symbol="AAPL",
            quantity=100,
            price=150.00
        ))
        
        # Test exceeding limits
        self.assertFalse(self.risk_manager.check_risk_limits(
            symbol="AAPL",
            quantity=1000000,
            price=150.00
        ))
        
    def test_position_tracking(self):
        """Test position tracking"""
        # Add position
        self.risk_manager.update_position(
            symbol="AAPL",
            quantity=100,
            price=150.00
        )
        
        # Check position
        self.assertIn("AAPL", self.risk_manager.positions)
        position = self.risk_manager.positions["AAPL"]
        self.assertEqual(position['quantity'], 100)
        self.assertEqual(position['avg_price'], 150.00)
        
        # Update position
        self.risk_manager.update_position(
            symbol="AAPL",
            quantity=50,
            price=160.00
        )
        
        # Check updated position
        position = self.risk_manager.positions["AAPL"]
        self.assertEqual(position['quantity'], 150)
        self.assertAlmostEqual(position['avg_price'], 153.33, places=2)
        
    def test_trade_recording(self):
        """Test trade recording"""
        # Record trade
        trade = {
            'timestamp': datetime.now(),
            'symbol': 'AAPL',
            'quantity': 100,
            'price': 150.00,
            'commission': 1.00,
            'slippage': 0.50
        }
        
        self.risk_manager.record_trade(trade)
        self.assertEqual(len(self.risk_manager.trades), 1)
        
    def test_risk_metrics(self):
        """Test risk metrics calculation"""
        # Record series of trades
        trades = [
            {'quantity': 100, 'price': 150.00},  # Win
            {'quantity': -100, 'price': 140.00}, # Loss
            {'quantity': 100, 'price': 160.00},  # Win
            {'quantity': -100, 'price': 150.00}  # Loss
        ]
        
        for trade in trades:
            self.risk_manager.record_trade({
                'timestamp': datetime.now(),
                'symbol': 'AAPL',
                'quantity': trade['quantity'],
                'price': trade['price'],
                'commission': 1.00,
                'slippage': 0.50
            })
            
        # Check metrics
        metrics = self.risk_manager.risk_metrics
        self.assertGreater(metrics['sharpe_ratio'], 0)
        self.assertLess(metrics['max_drawdown'], 0)
        self.assertGreater(metrics['win_rate'], 0)
        self.assertLess(metrics['win_rate'], 1)
        
    def test_risk_breaches(self):
        """Test risk breach detection"""
        # Create large drawdown
        for _ in range(10):
            self.risk_manager.record_trade({
                'timestamp': datetime.now(),
                'symbol': 'AAPL',
                'quantity': -100,
                'price': 140.00,
                'commission': 1.00,
                'slippage': 0.50
            })
            
        # Check risk breaches
        breaches = self.risk_manager.check_risk_limits()
        self.assertTrue(len(breaches) > 0)
        
    def test_position_limits_across_symbols(self):
        """Test position limits across multiple symbols"""
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        # Test within limits
        for symbol in symbols:
            self.assertTrue(self.risk_manager.check_position_limits(
                symbol=symbol,
                quantity=100,
                price=150.00
            ))
            
        # Test exceeding limits
        for symbol in symbols:
            self.assertFalse(self.risk_manager.check_position_limits(
                symbol=symbol,
                quantity=1000000,
                price=150.00
            ))
            
    def test_risk_limits_across_symbols(self):
        """Test risk limits across multiple symbols"""
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        # Test within limits
        for symbol in symbols:
            self.assertTrue(self.risk_manager.check_risk_limits(
                symbol=symbol,
                quantity=100,
                price=150.00
            ))
            
        # Test exceeding limits
        for symbol in symbols:
            self.assertFalse(self.risk_manager.check_risk_limits(
                symbol=symbol,
                quantity=1000000,
                price=150.00
            ))
            
    def test_capital_tracking(self):
        """Test capital tracking"""
        initial_capital = self.risk_manager.current_capital
        
        # Record profitable trade
        self.risk_manager.record_trade({
            'timestamp': datetime.now(),
            'symbol': 'AAPL',
            'quantity': 100,
            'price': 160.00,
            'commission': 1.00,
            'slippage': 0.50
        })
        
        # Check capital increased
        self.assertGreater(self.risk_manager.current_capital, initial_capital)
        
        # Record losing trade
        self.risk_manager.record_trade({
            'timestamp': datetime.now(),
            'symbol': 'AAPL',
            'quantity': -100,
            'price': 140.00,
            'commission': 1.00,
            'slippage': 0.50
        })
        
        # Check capital decreased
        self.assertLess(self.risk_manager.current_capital, initial_capital)

if __name__ == '__main__':
    unittest.main() 