"""
Test suite for performance tracker
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..performance_tracker import PerformanceTracker
from ..config import INITIAL_CAPITAL, RISK_FREE_RATE, RISK_LIMITS

class TestPerformanceTracker(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.performance = PerformanceTracker()
        
    def test_initial_state(self):
        """Test initial state of performance tracker"""
        self.assertEqual(self.performance.initial_capital, INITIAL_CAPITAL)
        self.assertEqual(self.performance.current_capital, INITIAL_CAPITAL)
        self.assertEqual(len(self.performance.positions), 0)
        self.assertEqual(len(self.performance.trades), 0)
        
    def test_position_update(self):
        """Test position update functionality"""
        # Test new position
        self.performance.update_position(
            symbol="AAPL",
            quantity=100,
            price=150.00,
            timestamp=datetime.now()
        )
        
        self.assertIn("AAPL", self.performance.positions)
        position = self.performance.positions["AAPL"]
        self.assertEqual(position['quantity'], 100)
        self.assertEqual(position['avg_price'], 150.00)
        
        # Test position increase
        self.performance.update_position(
            symbol="AAPL",
            quantity=50,
            price=160.00,
            timestamp=datetime.now()
        )
        
        position = self.performance.positions["AAPL"]
        self.assertEqual(position['quantity'], 150)
        self.assertAlmostEqual(position['avg_price'], 153.33, places=2)
        
        # Test position decrease
        self.performance.update_position(
            symbol="AAPL",
            quantity=-50,
            price=170.00,
            timestamp=datetime.now()
        )
        
        position = self.performance.positions["AAPL"]
        self.assertEqual(position['quantity'], 100)
        self.assertAlmostEqual(position['avg_price'], 153.33, places=2)
        
        # Test position close
        self.performance.update_position(
            symbol="AAPL",
            quantity=-100,
            price=180.00,
            timestamp=datetime.now()
        )
        
        self.assertEqual(position['quantity'], 0)
        self.assertEqual(position['avg_price'], 0)
        
    def test_trade_recording(self):
        """Test trade recording functionality"""
        # Record winning trade
        winning_trade = {
            'timestamp': datetime.now(),
            'symbol': 'AAPL',
            'quantity': 100,
            'price': 150.00,
            'commission': 1.00,
            'slippage': 0.50
        }
        
        self.performance.record_trade(winning_trade)
        self.assertEqual(len(self.performance.trades), 1)
        
        # Record losing trade
        losing_trade = {
            'timestamp': datetime.now(),
            'symbol': 'AAPL',
            'quantity': -100,
            'price': 140.00,
            'commission': 1.00,
            'slippage': 0.50
        }
        
        self.performance.record_trade(losing_trade)
        self.assertEqual(len(self.performance.trades), 2)
        
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
            self.performance.record_trade({
                'timestamp': datetime.now(),
                'symbol': 'AAPL',
                'quantity': trade['quantity'],
                'price': trade['price'],
                'commission': 1.00,
                'slippage': 0.50
            })
            
        # Check metrics
        metrics = self.performance.risk_metrics
        self.assertGreater(metrics['sharpe_ratio'], 0)
        self.assertLess(metrics['max_drawdown'], 0)
        self.assertGreater(metrics['win_rate'], 0)
        self.assertLess(metrics['win_rate'], 1)
        
    def test_risk_limits(self):
        """Test risk limit checking"""
        # Create large drawdown
        for _ in range(10):
            self.performance.record_trade({
                'timestamp': datetime.now(),
                'symbol': 'AAPL',
                'quantity': -100,
                'price': 140.00,
                'commission': 1.00,
                'slippage': 0.50
            })
            
        # Check risk limits
        breaches = self.performance.check_risk_limits()
        self.assertTrue(len(breaches) > 0)
        
    def test_performance_report(self):
        """Test performance report generation"""
        # Record some trades
        for _ in range(5):
            self.performance.record_trade({
                'timestamp': datetime.now(),
                'symbol': 'AAPL',
                'quantity': 100,
                'price': 150.00,
                'commission': 1.00,
                'slippage': 0.50
            })
            
        # Generate report
        report = self.performance.get_performance_report()
        
        # Check report structure
        self.assertIn('capital', report)
        self.assertIn('risk_metrics', report)
        self.assertIn('positions', report)
        self.assertIn('trade_statistics', report)
        
        # Check capital information
        self.assertEqual(report['capital']['initial'], INITIAL_CAPITAL)
        self.assertGreater(report['capital']['current'], 0)
        
        # Check trade statistics
        stats = report['trade_statistics']
        self.assertEqual(stats['total_trades'], 5)
        self.assertGreaterEqual(stats['winning_trades'], 0)
        self.assertGreaterEqual(stats['losing_trades'], 0)
        
    def test_position_tracking(self):
        """Test position tracking across multiple symbols"""
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        # Create positions for each symbol
        for symbol in symbols:
            self.performance.update_position(
                symbol=symbol,
                quantity=100,
                price=150.00,
                timestamp=datetime.now()
            )
            
        # Check positions
        self.assertEqual(len(self.performance.positions), len(symbols))
        for symbol in symbols:
            self.assertIn(symbol, self.performance.positions)
            position = self.performance.positions[symbol]
            self.assertEqual(position['quantity'], 100)
            self.assertEqual(position['avg_price'], 150.00)
            
    def test_capital_tracking(self):
        """Test capital tracking with trades"""
        initial_capital = self.performance.current_capital
        
        # Record profitable trade
        self.performance.record_trade({
            'timestamp': datetime.now(),
            'symbol': 'AAPL',
            'quantity': 100,
            'price': 160.00,
            'commission': 1.00,
            'slippage': 0.50
        })
        
        # Check capital increased
        self.assertGreater(self.performance.current_capital, initial_capital)
        
        # Record losing trade
        self.performance.record_trade({
            'timestamp': datetime.now(),
            'symbol': 'AAPL',
            'quantity': -100,
            'price': 140.00,
            'commission': 1.00,
            'slippage': 0.50
        })
        
        # Check capital decreased
        self.assertLess(self.performance.current_capital, initial_capital)

if __name__ == '__main__':
    unittest.main() 