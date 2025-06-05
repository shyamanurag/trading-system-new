"""
Test suite for trading strategy
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..trading_strategy import TradingStrategy
from ..config import STRATEGY_CONFIG, RISK_LIMITS

class TestTradingStrategy(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.strategy = TradingStrategy()
        
    def test_initial_state(self):
        """Test initial state of trading strategy"""
        self.assertEqual(len(self.strategy.positions), 0)
        self.assertEqual(len(self.strategy.trades), 0)
        self.assertEqual(self.strategy.current_capital, 0)
        
    def test_signal_generation(self):
        """Test signal generation"""
        # Create dummy data
        data = pd.DataFrame({
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randn(100)
        })
        
        # Generate signals
        signals = self.strategy.generate_signals(data)
        
        # Check signals
        self.assertIsNotNone(signals)
        self.assertEqual(len(signals), len(data))
        self.assertTrue(all(signal in [-1, 0, 1] for signal in signals))
        
    def test_position_sizing(self):
        """Test position sizing"""
        # Test within limits
        size = self.strategy.calculate_position_size(
            symbol="AAPL",
            price=150.00,
            signal=1
        )
        
        self.assertGreater(size, 0)
        self.assertLessEqual(size * 150.00, STRATEGY_CONFIG['max_position_size'])
        
        # Test exceeding limits
        size = self.strategy.calculate_position_size(
            symbol="AAPL",
            price=150.00,
            signal=1,
            max_size=1000000
        )
        
        self.assertLessEqual(size * 150.00, STRATEGY_CONFIG['max_position_size'])
        
    def test_entry_rules(self):
        """Test entry rules"""
        # Create dummy data
        data = pd.DataFrame({
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randn(100)
        })
        
        # Test entry rules
        entry = self.strategy.check_entry_rules(data)
        
        # Check entry
        self.assertIsNotNone(entry)
        self.assertTrue(isinstance(entry, bool))
        
    def test_exit_rules(self):
        """Test exit rules"""
        # Create dummy data
        data = pd.DataFrame({
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randn(100)
        })
        
        # Test exit rules
        exit = self.strategy.check_exit_rules(data)
        
        # Check exit
        self.assertIsNotNone(exit)
        self.assertTrue(isinstance(exit, bool))
        
    def test_risk_management(self):
        """Test risk management"""
        # Test within limits
        risk = self.strategy.check_risk_limits(
            symbol="AAPL",
            quantity=100,
            price=150.00
        )
        
        self.assertTrue(risk)
        
        # Test exceeding limits
        risk = self.strategy.check_risk_limits(
            symbol="AAPL",
            quantity=1000000,
            price=150.00
        )
        
        self.assertFalse(risk)
        
    def test_position_tracking(self):
        """Test position tracking"""
        # Add position
        self.strategy.update_position(
            symbol="AAPL",
            quantity=100,
            price=150.00
        )
        
        # Check position
        self.assertIn("AAPL", self.strategy.positions)
        position = self.strategy.positions["AAPL"]
        self.assertEqual(position['quantity'], 100)
        self.assertEqual(position['avg_price'], 150.00)
        
        # Update position
        self.strategy.update_position(
            symbol="AAPL",
            quantity=50,
            price=160.00
        )
        
        # Check updated position
        position = self.strategy.positions["AAPL"]
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
        
        self.strategy.record_trade(trade)
        self.assertEqual(len(self.strategy.trades), 1)
        
    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        # Record series of trades
        trades = [
            {'quantity': 100, 'price': 150.00},  # Win
            {'quantity': -100, 'price': 140.00}, # Loss
            {'quantity': 100, 'price': 160.00},  # Win
            {'quantity': -100, 'price': 150.00}  # Loss
        ]
        
        for trade in trades:
            self.strategy.record_trade({
                'timestamp': datetime.now(),
                'symbol': 'AAPL',
                'quantity': trade['quantity'],
                'price': trade['price'],
                'commission': 1.00,
                'slippage': 0.50
            })
            
        # Check metrics
        metrics = self.strategy.calculate_performance_metrics()
        self.assertGreater(metrics['sharpe_ratio'], 0)
        self.assertLess(metrics['max_drawdown'], 0)
        self.assertGreater(metrics['win_rate'], 0)
        self.assertLess(metrics['win_rate'], 1)
        
    def test_strategy_optimization(self):
        """Test strategy optimization"""
        # Create dummy data
        data = pd.DataFrame({
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randn(100)
        })
        
        # Optimize strategy
        best_params = self.strategy.optimize_parameters(data)
        
        # Check best parameters
        self.assertIsNotNone(best_params)
        self.assertTrue(all(param in STRATEGY_CONFIG['parameters'] for param in best_params))
        
    def test_strategy_backtesting(self):
        """Test strategy backtesting"""
        # Create dummy data
        data = pd.DataFrame({
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randn(100)
        })
        
        # Backtest strategy
        results = self.strategy.backtest(data)
        
        # Check results
        self.assertIsNotNone(results)
        self.assertIn('returns', results)
        self.assertIn('sharpe_ratio', results)
        self.assertIn('max_drawdown', results)
        self.assertIn('win_rate', results)

if __name__ == '__main__':
    unittest.main() 