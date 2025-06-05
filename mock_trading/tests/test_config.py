"""
Test suite for configuration
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..config import (
    START_DATE,
    END_DATE,
    INITIAL_CAPITAL,
    RISK_FREE_RATE,
    DATA_CONFIG,
    MODEL_CONFIG,
    STRATEGY_CONFIG,
    RISK_LIMITS,
    POSITION_LIMITS
)

class TestConfig(unittest.TestCase):
    def test_dates(self):
        """Test date configuration"""
        # Check start date
        self.assertIsInstance(START_DATE, datetime)
        
        # Check end date
        self.assertIsInstance(END_DATE, datetime)
        
        # Check date range
        self.assertLess(START_DATE, END_DATE)
        
    def test_capital(self):
        """Test capital configuration"""
        # Check initial capital
        self.assertIsInstance(INITIAL_CAPITAL, float)
        self.assertGreater(INITIAL_CAPITAL, 0)
        
    def test_risk_free_rate(self):
        """Test risk-free rate configuration"""
        # Check risk-free rate
        self.assertIsInstance(RISK_FREE_RATE, float)
        self.assertGreaterEqual(RISK_FREE_RATE, 0)
        self.assertLessEqual(RISK_FREE_RATE, 1)
        
    def test_data_config(self):
        """Test data configuration"""
        # Check symbols
        self.assertIn('symbols', DATA_CONFIG)
        self.assertIsInstance(DATA_CONFIG['symbols'], list)
        self.assertGreater(len(DATA_CONFIG['symbols']), 0)
        
        # Check features
        self.assertIn('features', DATA_CONFIG)
        self.assertIsInstance(DATA_CONFIG['features'], list)
        self.assertGreater(len(DATA_CONFIG['features']), 0)
        
        # Check data source
        self.assertIn('data_source', DATA_CONFIG)
        self.assertIsInstance(DATA_CONFIG['data_source'], str)
        
    def test_model_config(self):
        """Test model configuration"""
        # Check model type
        self.assertIn('model_type', MODEL_CONFIG)
        self.assertIsInstance(MODEL_CONFIG['model_type'], str)
        
        # Check hyperparameters
        self.assertIn('hyperparameters', MODEL_CONFIG)
        self.assertIsInstance(MODEL_CONFIG['hyperparameters'], dict)
        self.assertGreater(len(MODEL_CONFIG['hyperparameters']), 0)
        
        # Check feature selection
        self.assertIn('feature_selection', MODEL_CONFIG)
        self.assertIsInstance(MODEL_CONFIG['feature_selection'], bool)
        
    def test_strategy_config(self):
        """Test strategy configuration"""
        # Check strategy type
        self.assertIn('strategy_type', STRATEGY_CONFIG)
        self.assertIsInstance(STRATEGY_CONFIG['strategy_type'], str)
        
        # Check parameters
        self.assertIn('parameters', STRATEGY_CONFIG)
        self.assertIsInstance(STRATEGY_CONFIG['parameters'], dict)
        self.assertGreater(len(STRATEGY_CONFIG['parameters']), 0)
        
        # Check position sizing
        self.assertIn('position_sizing', STRATEGY_CONFIG)
        self.assertIsInstance(STRATEGY_CONFIG['position_sizing'], str)
        
        # Check max position size
        self.assertIn('max_position_size', STRATEGY_CONFIG)
        self.assertIsInstance(STRATEGY_CONFIG['max_position_size'], float)
        self.assertGreater(STRATEGY_CONFIG['max_position_size'], 0)
        
    def test_risk_limits(self):
        """Test risk limits configuration"""
        # Check max drawdown
        self.assertIn('max_drawdown', RISK_LIMITS)
        self.assertIsInstance(RISK_LIMITS['max_drawdown'], float)
        self.assertLess(RISK_LIMITS['max_drawdown'], 0)
        
        # Check max position size
        self.assertIn('max_position_size', RISK_LIMITS)
        self.assertIsInstance(RISK_LIMITS['max_position_size'], float)
        self.assertGreater(RISK_LIMITS['max_position_size'], 0)
        
        # Check max leverage
        self.assertIn('max_leverage', RISK_LIMITS)
        self.assertIsInstance(RISK_LIMITS['max_leverage'], float)
        self.assertGreater(RISK_LIMITS['max_leverage'], 0)
        
    def test_position_limits(self):
        """Test position limits configuration"""
        # Check max positions
        self.assertIn('max_positions', POSITION_LIMITS)
        self.assertIsInstance(POSITION_LIMITS['max_positions'], int)
        self.assertGreater(POSITION_LIMITS['max_positions'], 0)
        
        # Check max position size
        self.assertIn('max_position_size', POSITION_LIMITS)
        self.assertIsInstance(POSITION_LIMITS['max_position_size'], float)
        self.assertGreater(POSITION_LIMITS['max_position_size'], 0)
        
        # Check max position value
        self.assertIn('max_position_value', POSITION_LIMITS)
        self.assertIsInstance(POSITION_LIMITS['max_position_value'], float)
        self.assertGreater(POSITION_LIMITS['max_position_value'], 0)
        
    def test_config_consistency(self):
        """Test configuration consistency"""
        # Check position size consistency
        self.assertEqual(
            STRATEGY_CONFIG['max_position_size'],
            RISK_LIMITS['max_position_size']
        )
        self.assertEqual(
            STRATEGY_CONFIG['max_position_size'],
            POSITION_LIMITS['max_position_size']
        )
        
        # Check data consistency
        self.assertTrue(all(symbol in DATA_CONFIG['symbols'] for symbol in STRATEGY_CONFIG['symbols']))
        
        # Check feature consistency
        self.assertTrue(all(feature in DATA_CONFIG['features'] for feature in MODEL_CONFIG['features']))

if __name__ == '__main__':
    unittest.main() 