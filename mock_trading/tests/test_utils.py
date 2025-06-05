"""
Test suite for utility functions
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..utils import (
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_position_size,
    calculate_commission,
    calculate_slippage,
    format_currency,
    format_percentage,
    format_timestamp,
    validate_data,
    validate_features,
    preprocess_data,
    preprocess_features,
    split_data,
    split_features,
    scale_data,
    scale_features
)

class TestUtils(unittest.TestCase):
    def test_calculate_returns(self):
        """Test return calculation"""
        # Test positive returns
        returns = calculate_returns(100, 110)
        self.assertEqual(returns, 0.10)
        
        # Test negative returns
        returns = calculate_returns(100, 90)
        self.assertEqual(returns, -0.10)
        
        # Test zero returns
        returns = calculate_returns(100, 100)
        self.assertEqual(returns, 0.00)
        
    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        # Create dummy returns
        returns = pd.Series([0.01, 0.02, -0.01, 0.03, -0.02])
        
        # Calculate Sharpe ratio
        sharpe = calculate_sharpe_ratio(returns)
        
        # Check Sharpe ratio
        self.assertIsNotNone(sharpe)
        self.assertIsInstance(sharpe, float)
        
    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation"""
        # Create dummy prices
        prices = pd.Series([100, 110, 105, 115, 100])
        
        # Calculate maximum drawdown
        drawdown = calculate_max_drawdown(prices)
        
        # Check maximum drawdown
        self.assertIsNotNone(drawdown)
        self.assertIsInstance(drawdown, float)
        self.assertLessEqual(drawdown, 0)
        
    def test_calculate_win_rate(self):
        """Test win rate calculation"""
        # Create dummy trades
        trades = [
            {'quantity': 100, 'price': 150.00},  # Win
            {'quantity': -100, 'price': 140.00}, # Loss
            {'quantity': 100, 'price': 160.00},  # Win
            {'quantity': -100, 'price': 150.00}  # Loss
        ]
        
        # Calculate win rate
        win_rate = calculate_win_rate(trades)
        
        # Check win rate
        self.assertIsNotNone(win_rate)
        self.assertIsInstance(win_rate, float)
        self.assertGreaterEqual(win_rate, 0)
        self.assertLessEqual(win_rate, 1)
        
    def test_calculate_position_size(self):
        """Test position size calculation"""
        # Test within limits
        size = calculate_position_size(
            capital=100000,
            price=150.00,
            risk_per_trade=0.02
        )
        
        self.assertGreater(size, 0)
        self.assertLessEqual(size * 150.00, 100000)
        
        # Test exceeding limits
        size = calculate_position_size(
            capital=100000,
            price=150.00,
            risk_per_trade=0.02,
            max_size=1000000
        )
        
        self.assertLessEqual(size * 150.00, 100000)
        
    def test_calculate_commission(self):
        """Test commission calculation"""
        # Test minimum commission
        commission = calculate_commission(100)
        self.assertGreaterEqual(commission, 1.00)
        
        # Test maximum commission
        commission = calculate_commission(1000000)
        self.assertLessEqual(commission, 50.00)
        
        # Test proportional commission
        commission1 = calculate_commission(1000)
        commission2 = calculate_commission(2000)
        self.assertGreater(commission2, commission1)
        
    def test_calculate_slippage(self):
        """Test slippage calculation"""
        # Test small order
        slippage = calculate_slippage(1000, 'MARKET')
        self.assertGreaterEqual(slippage, 0)
        
        # Test large order
        slippage = calculate_slippage(1000000, 'MARKET')
        self.assertGreaterEqual(slippage, 0)
        
    def test_format_currency(self):
        """Test currency formatting"""
        # Test positive amount
        formatted = format_currency(1000.50)
        self.assertEqual(formatted, '$1,000.50')
        
        # Test negative amount
        formatted = format_currency(-1000.50)
        self.assertEqual(formatted, '-$1,000.50')
        
        # Test zero amount
        formatted = format_currency(0.00)
        self.assertEqual(formatted, '$0.00')
        
    def test_format_percentage(self):
        """Test percentage formatting"""
        # Test positive percentage
        formatted = format_percentage(0.1050)
        self.assertEqual(formatted, '10.50%')
        
        # Test negative percentage
        formatted = format_percentage(-0.1050)
        self.assertEqual(formatted, '-10.50%')
        
        # Test zero percentage
        formatted = format_percentage(0.0000)
        self.assertEqual(formatted, '0.00%')
        
    def test_format_timestamp(self):
        """Test timestamp formatting"""
        # Test timestamp
        timestamp = datetime.now()
        formatted = format_timestamp(timestamp)
        self.assertIsInstance(formatted, str)
        
    def test_validate_data(self):
        """Test data validation"""
        # Create valid data
        data = pd.DataFrame({
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randn(100)
        })
        
        # Validate data
        self.assertTrue(validate_data(data))
        
        # Create invalid data
        data = pd.DataFrame({
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randn(100)
        })
        data.loc[0, 'high'] = data.loc[0, 'low'] - 1
        
        # Validate data
        self.assertFalse(validate_data(data))
        
    def test_validate_features(self):
        """Test feature validation"""
        # Create valid features
        features = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        
        # Validate features
        self.assertTrue(validate_features(features))
        
        # Create invalid features
        features = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        features.loc[0, 'feature1'] = np.nan
        
        # Validate features
        self.assertFalse(validate_features(features))
        
    def test_preprocess_data(self):
        """Test data preprocessing"""
        # Create data
        data = pd.DataFrame({
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randn(100)
        })
        
        # Preprocess data
        processed_data = preprocess_data(data)
        
        # Check processed data
        self.assertIsInstance(processed_data, pd.DataFrame)
        self.assertEqual(len(processed_data), len(data))
        self.assertTrue(all(col in processed_data.columns for col in data.columns))
        
    def test_preprocess_features(self):
        """Test feature preprocessing"""
        # Create features
        features = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        
        # Preprocess features
        processed_features = preprocess_features(features)
        
        # Check processed features
        self.assertIsInstance(processed_features, pd.DataFrame)
        self.assertEqual(len(processed_features), len(features))
        self.assertTrue(all(col in processed_features.columns for col in features.columns))
        
    def test_split_data(self):
        """Test data splitting"""
        # Create data
        data = pd.DataFrame({
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randn(100)
        })
        
        # Split data
        train_data, test_data = split_data(data)
        
        # Check split data
        self.assertIsInstance(train_data, pd.DataFrame)
        self.assertIsInstance(test_data, pd.DataFrame)
        self.assertEqual(len(train_data) + len(test_data), len(data))
        self.assertTrue(all(col in train_data.columns for col in data.columns))
        self.assertTrue(all(col in test_data.columns for col in data.columns))
        
    def test_split_features(self):
        """Test feature splitting"""
        # Create features
        features = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        
        # Split features
        train_features, test_features = split_features(features)
        
        # Check split features
        self.assertIsInstance(train_features, pd.DataFrame)
        self.assertIsInstance(test_features, pd.DataFrame)
        self.assertEqual(len(train_features) + len(test_features), len(features))
        self.assertTrue(all(col in train_features.columns for col in features.columns))
        self.assertTrue(all(col in test_features.columns for col in features.columns))
        
    def test_scale_data(self):
        """Test data scaling"""
        # Create data
        data = pd.DataFrame({
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randn(100)
        })
        
        # Scale data
        scaled_data = scale_data(data)
        
        # Check scaled data
        self.assertIsInstance(scaled_data, pd.DataFrame)
        self.assertEqual(len(scaled_data), len(data))
        self.assertTrue(all(col in scaled_data.columns for col in data.columns))
        
    def test_scale_features(self):
        """Test feature scaling"""
        # Create features
        features = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        
        # Scale features
        scaled_features = scale_features(features)
        
        # Check scaled features
        self.assertIsInstance(scaled_features, pd.DataFrame)
        self.assertEqual(len(scaled_features), len(features))
        self.assertTrue(all(col in scaled_features.columns for col in features.columns))

if __name__ == '__main__':
    unittest.main() 