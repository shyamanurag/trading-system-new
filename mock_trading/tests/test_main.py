"""
Test suite for main application
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..main import (
    initialize_components,
    load_data,
    train_model,
    backtest_strategy,
    run_live_trading,
    generate_report
)

class TestMain(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.components = initialize_components()
        
    def test_initialization(self):
        """Test component initialization"""
        # Check components
        self.assertIn('data_loader', self.components)
        self.assertIn('market_simulator', self.components)
        self.assertIn('trading_engine', self.components)
        self.assertIn('risk_manager', self.components)
        self.assertIn('performance_tracker', self.components)
        self.assertIn('ml_model', self.components)
        self.assertIn('trading_strategy', self.components)
        
    def test_data_loading(self):
        """Test data loading"""
        # Load data
        data = load_data(self.components['data_loader'])
        
        # Check data
        self.assertIsNotNone(data)
        self.assertIsInstance(data, dict)
        self.assertGreater(len(data), 0)
        
    def test_model_training(self):
        """Test model training"""
        # Load data
        data = load_data(self.components['data_loader'])
        
        # Train model
        model = train_model(
            self.components['ml_model'],
            data
        )
        
        # Check model
        self.assertIsNotNone(model)
        
    def test_strategy_backtesting(self):
        """Test strategy backtesting"""
        # Load data
        data = load_data(self.components['data_loader'])
        
        # Train model
        model = train_model(
            self.components['ml_model'],
            data
        )
        
        # Backtest strategy
        results = backtest_strategy(
            self.components['trading_strategy'],
            self.components['market_simulator'],
            self.components['trading_engine'],
            self.components['risk_manager'],
            self.components['performance_tracker'],
            data,
            model
        )
        
        # Check results
        self.assertIsNotNone(results)
        self.assertIn('returns', results)
        self.assertIn('sharpe_ratio', results)
        self.assertIn('max_drawdown', results)
        self.assertIn('win_rate', results)
        
    def test_live_trading(self):
        """Test live trading"""
        # Load data
        data = load_data(self.components['data_loader'])
        
        # Train model
        model = train_model(
            self.components['ml_model'],
            data
        )
        
        # Run live trading
        results = run_live_trading(
            self.components['trading_strategy'],
            self.components['market_simulator'],
            self.components['trading_engine'],
            self.components['risk_manager'],
            self.components['performance_tracker'],
            data,
            model
        )
        
        # Check results
        self.assertIsNotNone(results)
        self.assertIn('returns', results)
        self.assertIn('sharpe_ratio', results)
        self.assertIn('max_drawdown', results)
        self.assertIn('win_rate', results)
        
    def test_report_generation(self):
        """Test report generation"""
        # Load data
        data = load_data(self.components['data_loader'])
        
        # Train model
        model = train_model(
            self.components['ml_model'],
            data
        )
        
        # Backtest strategy
        results = backtest_strategy(
            self.components['trading_strategy'],
            self.components['market_simulator'],
            self.components['trading_engine'],
            self.components['risk_manager'],
            self.components['performance_tracker'],
            data,
            model
        )
        
        # Generate report
        report = generate_report(results)
        
        # Check report
        self.assertIsNotNone(report)
        self.assertIsInstance(report, str)
        
    def test_end_to_end(self):
        """Test end-to-end workflow"""
        # Load data
        data = load_data(self.components['data_loader'])
        
        # Train model
        model = train_model(
            self.components['ml_model'],
            data
        )
        
        # Backtest strategy
        backtest_results = backtest_strategy(
            self.components['trading_strategy'],
            self.components['market_simulator'],
            self.components['trading_engine'],
            self.components['risk_manager'],
            self.components['performance_tracker'],
            data,
            model
        )
        
        # Run live trading
        live_results = run_live_trading(
            self.components['trading_strategy'],
            self.components['market_simulator'],
            self.components['trading_engine'],
            self.components['risk_manager'],
            self.components['performance_tracker'],
            data,
            model
        )
        
        # Generate reports
        backtest_report = generate_report(backtest_results)
        live_report = generate_report(live_results)
        
        # Check reports
        self.assertIsNotNone(backtest_report)
        self.assertIsNotNone(live_report)
        self.assertIsInstance(backtest_report, str)
        self.assertIsInstance(live_report, str)

if __name__ == '__main__':
    unittest.main() 