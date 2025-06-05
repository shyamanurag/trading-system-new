"""
Test suite for data loader
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..data_loader import DataLoader
from ..config import START_DATE, END_DATE, DATA_CONFIG

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.data_loader = DataLoader()
        
    def test_initial_state(self):
        """Test initial state of data loader"""
        self.assertEqual(len(self.data_loader.data), 0)
        self.assertEqual(len(self.data_loader.features), 0)
        
    def test_data_loading(self):
        """Test data loading functionality"""
        # Load data
        self.data_loader.load_data()
        
        # Check data structure
        self.assertGreater(len(self.data_loader.data), 0)
        self.assertGreater(len(self.data_loader.features), 0)
        
        # Check data for each symbol
        for symbol in DATA_CONFIG['symbols']:
            self.assertIn(symbol, self.data_loader.data)
            data = self.data_loader.data[symbol]
            
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
            
    def test_feature_engineering(self):
        """Test feature engineering functionality"""
        # Load data
        self.data_loader.load_data()
        
        # Check features
        self.assertGreater(len(self.data_loader.features), 0)
        
        # Check feature structure
        for symbol in DATA_CONFIG['symbols']:
            self.assertIn(symbol, self.data_loader.features)
            features = self.data_loader.features[symbol]
            
            # Check feature structure
            self.assertIsInstance(features, pd.DataFrame)
            self.assertTrue(all(col in features.columns for col in DATA_CONFIG['features']))
            
            # Check feature quality
            self.assertFalse(features.isnull().any().any())
            
    def test_data_validation(self):
        """Test data validation functionality"""
        # Load data
        self.data_loader.load_data()
        
        # Check data validation
        for symbol in DATA_CONFIG['symbols']:
            data = self.data_loader.data[symbol]
            
            # Check data validation
            self.assertTrue(self.data_loader.validate_data(data))
            
    def test_feature_validation(self):
        """Test feature validation functionality"""
        # Load data
        self.data_loader.load_data()
        
        # Check feature validation
        for symbol in DATA_CONFIG['symbols']:
            features = self.data_loader.features[symbol]
            
            # Check feature validation
            self.assertTrue(self.data_loader.validate_features(features))
            
    def test_data_preprocessing(self):
        """Test data preprocessing functionality"""
        # Load data
        self.data_loader.load_data()
        
        # Check data preprocessing
        for symbol in DATA_CONFIG['symbols']:
            data = self.data_loader.data[symbol]
            processed_data = self.data_loader.preprocess_data(data)
            
            # Check processed data structure
            self.assertIsInstance(processed_data, pd.DataFrame)
            self.assertTrue(all(col in processed_data.columns for col in DATA_CONFIG['features']))
            
            # Check processed data quality
            self.assertFalse(processed_data.isnull().any().any())
            self.assertTrue(all(processed_data['high'] >= processed_data['low']))
            self.assertTrue(all(processed_data['ask'] >= processed_data['bid']))
            
    def test_feature_preprocessing(self):
        """Test feature preprocessing functionality"""
        # Load data
        self.data_loader.load_data()
        
        # Check feature preprocessing
        for symbol in DATA_CONFIG['symbols']:
            features = self.data_loader.features[symbol]
            processed_features = self.data_loader.preprocess_features(features)
            
            # Check processed feature structure
            self.assertIsInstance(processed_features, pd.DataFrame)
            self.assertTrue(all(col in processed_features.columns for col in DATA_CONFIG['features']))
            
            # Check processed feature quality
            self.assertFalse(processed_features.isnull().any().any())
            
    def test_data_splitting(self):
        """Test data splitting functionality"""
        # Load data
        self.data_loader.load_data()
        
        # Check data splitting
        for symbol in DATA_CONFIG['symbols']:
            data = self.data_loader.data[symbol]
            train_data, test_data = self.data_loader.split_data(data)
            
            # Check split data structure
            self.assertIsInstance(train_data, pd.DataFrame)
            self.assertIsInstance(test_data, pd.DataFrame)
            self.assertTrue(all(col in train_data.columns for col in DATA_CONFIG['features']))
            self.assertTrue(all(col in test_data.columns for col in DATA_CONFIG['features']))
            
            # Check split data quality
            self.assertFalse(train_data.isnull().any().any())
            self.assertFalse(test_data.isnull().any().any())
            self.assertTrue(all(train_data['high'] >= train_data['low']))
            self.assertTrue(all(test_data['high'] >= test_data['low']))
            self.assertTrue(all(train_data['ask'] >= train_data['bid']))
            self.assertTrue(all(test_data['ask'] >= test_data['bid']))
            
    def test_feature_splitting(self):
        """Test feature splitting functionality"""
        # Load data
        self.data_loader.load_data()
        
        # Check feature splitting
        for symbol in DATA_CONFIG['symbols']:
            features = self.data_loader.features[symbol]
            train_features, test_features = self.data_loader.split_features(features)
            
            # Check split feature structure
            self.assertIsInstance(train_features, pd.DataFrame)
            self.assertIsInstance(test_features, pd.DataFrame)
            self.assertTrue(all(col in train_features.columns for col in DATA_CONFIG['features']))
            self.assertTrue(all(col in test_features.columns for col in DATA_CONFIG['features']))
            
            # Check split feature quality
            self.assertFalse(train_features.isnull().any().any())
            self.assertFalse(test_features.isnull().any().any())
            
    def test_data_scaling(self):
        """Test data scaling functionality"""
        # Load data
        self.data_loader.load_data()
        
        # Check data scaling
        for symbol in DATA_CONFIG['symbols']:
            data = self.data_loader.data[symbol]
            scaled_data = self.data_loader.scale_data(data)
            
            # Check scaled data structure
            self.assertIsInstance(scaled_data, pd.DataFrame)
            self.assertTrue(all(col in scaled_data.columns for col in DATA_CONFIG['features']))
            
            # Check scaled data quality
            self.assertFalse(scaled_data.isnull().any().any())
            self.assertTrue(all(scaled_data['high'] >= scaled_data['low']))
            self.assertTrue(all(scaled_data['ask'] >= scaled_data['bid']))
            
    def test_feature_scaling(self):
        """Test feature scaling functionality"""
        # Load data
        self.data_loader.load_data()
        
        # Check feature scaling
        for symbol in DATA_CONFIG['symbols']:
            features = self.data_loader.features[symbol]
            scaled_features = self.data_loader.scale_features(features)
            
            # Check scaled feature structure
            self.assertIsInstance(scaled_features, pd.DataFrame)
            self.assertTrue(all(col in scaled_features.columns for col in DATA_CONFIG['features']))
            
            # Check scaled feature quality
            self.assertFalse(scaled_features.isnull().any().any())

if __name__ == '__main__':
    unittest.main() 