"""
Test suite for ML model
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..ml_model import MLModel
from ..config import MODEL_CONFIG, FEATURE_CONFIG

class TestMLModel(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.model = MLModel()
        
    def test_initial_state(self):
        """Test initial state of ML model"""
        self.assertIsNone(self.model.model)
        self.assertEqual(len(self.model.features), 0)
        self.assertEqual(len(self.model.predictions), 0)
        
    def test_model_initialization(self):
        """Test model initialization"""
        # Initialize model
        self.model.initialize_model()
        
        # Check model
        self.assertIsNotNone(self.model.model)
        
    def test_feature_selection(self):
        """Test feature selection"""
        # Initialize model
        self.model.initialize_model()
        
        # Select features
        self.model.select_features()
        
        # Check features
        self.assertGreater(len(self.model.features), 0)
        self.assertTrue(all(feature in FEATURE_CONFIG['features'] for feature in self.model.features))
        
    def test_model_training(self):
        """Test model training"""
        # Initialize model
        self.model.initialize_model()
        
        # Select features
        self.model.select_features()
        
        # Create dummy data
        X_train = pd.DataFrame(np.random.randn(100, len(self.model.features)), columns=self.model.features)
        y_train = pd.Series(np.random.randint(0, 2, 100))
        
        # Train model
        self.model.train(X_train, y_train)
        
        # Check model
        self.assertIsNotNone(self.model.model)
        
    def test_model_prediction(self):
        """Test model prediction"""
        # Initialize model
        self.model.initialize_model()
        
        # Select features
        self.model.select_features()
        
        # Create dummy data
        X_train = pd.DataFrame(np.random.randn(100, len(self.model.features)), columns=self.model.features)
        y_train = pd.Series(np.random.randint(0, 2, 100))
        
        # Train model
        self.model.train(X_train, y_train)
        
        # Create test data
        X_test = pd.DataFrame(np.random.randn(10, len(self.model.features)), columns=self.model.features)
        
        # Make predictions
        predictions = self.model.predict(X_test)
        
        # Check predictions
        self.assertIsNotNone(predictions)
        self.assertEqual(len(predictions), len(X_test))
        self.assertTrue(all(pred in [0, 1] for pred in predictions))
        
    def test_model_evaluation(self):
        """Test model evaluation"""
        # Initialize model
        self.model.initialize_model()
        
        # Select features
        self.model.select_features()
        
        # Create dummy data
        X_train = pd.DataFrame(np.random.randn(100, len(self.model.features)), columns=self.model.features)
        y_train = pd.Series(np.random.randint(0, 2, 100))
        
        # Train model
        self.model.train(X_train, y_train)
        
        # Create test data
        X_test = pd.DataFrame(np.random.randn(10, len(self.model.features)), columns=self.model.features)
        y_test = pd.Series(np.random.randint(0, 2, 10))
        
        # Evaluate model
        metrics = self.model.evaluate(X_test, y_test)
        
        # Check metrics
        self.assertIsNotNone(metrics)
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1_score', metrics)
        
    def test_model_saving(self):
        """Test model saving"""
        # Initialize model
        self.model.initialize_model()
        
        # Select features
        self.model.select_features()
        
        # Create dummy data
        X_train = pd.DataFrame(np.random.randn(100, len(self.model.features)), columns=self.model.features)
        y_train = pd.Series(np.random.randint(0, 2, 100))
        
        # Train model
        self.model.train(X_train, y_train)
        
        # Save model
        self.model.save_model('test_model.pkl')
        
        # Check model file
        import os
        self.assertTrue(os.path.exists('test_model.pkl'))
        
        # Clean up
        os.remove('test_model.pkl')
        
    def test_model_loading(self):
        """Test model loading"""
        # Initialize model
        self.model.initialize_model()
        
        # Select features
        self.model.select_features()
        
        # Create dummy data
        X_train = pd.DataFrame(np.random.randn(100, len(self.model.features)), columns=self.model.features)
        y_train = pd.Series(np.random.randint(0, 2, 100))
        
        # Train model
        self.model.train(X_train, y_train)
        
        # Save model
        self.model.save_model('test_model.pkl')
        
        # Load model
        loaded_model = MLModel()
        loaded_model.load_model('test_model.pkl')
        
        # Check loaded model
        self.assertIsNotNone(loaded_model.model)
        self.assertEqual(len(loaded_model.features), len(self.model.features))
        
        # Clean up
        import os
        os.remove('test_model.pkl')
        
    def test_model_hyperparameter_tuning(self):
        """Test model hyperparameter tuning"""
        # Initialize model
        self.model.initialize_model()
        
        # Select features
        self.model.select_features()
        
        # Create dummy data
        X_train = pd.DataFrame(np.random.randn(100, len(self.model.features)), columns=self.model.features)
        y_train = pd.Series(np.random.randint(0, 2, 100))
        
        # Tune hyperparameters
        best_params = self.model.tune_hyperparameters(X_train, y_train)
        
        # Check best parameters
        self.assertIsNotNone(best_params)
        self.assertTrue(all(param in MODEL_CONFIG['hyperparameters'] for param in best_params))
        
    def test_model_cross_validation(self):
        """Test model cross validation"""
        # Initialize model
        self.model.initialize_model()
        
        # Select features
        self.model.select_features()
        
        # Create dummy data
        X = pd.DataFrame(np.random.randn(100, len(self.model.features)), columns=self.model.features)
        y = pd.Series(np.random.randint(0, 2, 100))
        
        # Perform cross validation
        cv_scores = self.model.cross_validate(X, y)
        
        # Check cross validation scores
        self.assertIsNotNone(cv_scores)
        self.assertIn('mean', cv_scores)
        self.assertIn('std', cv_scores)
        
    def test_model_feature_importance(self):
        """Test model feature importance"""
        # Initialize model
        self.model.initialize_model()
        
        # Select features
        self.model.select_features()
        
        # Create dummy data
        X_train = pd.DataFrame(np.random.randn(100, len(self.model.features)), columns=self.model.features)
        y_train = pd.Series(np.random.randint(0, 2, 100))
        
        # Train model
        self.model.train(X_train, y_train)
        
        # Get feature importance
        importance = self.model.get_feature_importance()
        
        # Check feature importance
        self.assertIsNotNone(importance)
        self.assertEqual(len(importance), len(self.model.features))
        self.assertTrue(all(imp >= 0 for imp in importance))

if __name__ == '__main__':
    unittest.main() 