"""
Unit tests for options pricing models
Validates mathematical accuracy against known values
"""

import unittest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.math.options_pricing import OptionsPricingModels, Greeks, quick_black_scholes, quick_greeks

class TestOptionsPricingModels(unittest.TestCase):
    """Test suite for options pricing models"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = OptionsPricingModels()
        self.tolerance = 0.01  # 1 cent tolerance for price comparisons
        
    def test_black_scholes_call_basic(self):
        """Test Black-Scholes call pricing with known values"""
        # Standard test case: S=100, K=100, T=1, r=0.05, sigma=0.2
        call_price = self.model.black_scholes_call(100, 100, 1.0, 0.05, 0.2)
        expected_price = 10.4506  # Known theoretical value
        
        self.assertAlmostEqual(call_price, expected_price, places=2,
                              msg=f"Call price {call_price} should be close to {expected_price}")
    
    def test_black_scholes_put_basic(self):
        """Test Black-Scholes put pricing with known values"""
        # Standard test case: S=100, K=100, T=1, r=0.05, sigma=0.2
        put_price = self.model.black_scholes_put(100, 100, 1.0, 0.05, 0.2)
        expected_price = 5.5735  # Known theoretical value
        
        self.assertAlmostEqual(put_price, expected_price, places=2,
                              msg=f"Put price {put_price} should be close to {expected_price}")
    
    def test_black_scholes_itm_call(self):
        """Test in-the-money call option"""
        # ITM call: S=110, K=100
        call_price = self.model.black_scholes_call(110, 100, 1.0, 0.05, 0.2)
        
        # ITM call should be worth more than intrinsic value
        intrinsic_value = 110 - 100
        self.assertGreater(call_price, intrinsic_value,
                          msg="ITM call should be worth more than intrinsic value")
    
    def test_black_scholes_otm_put(self):
        """Test out-of-the-money put option"""
        # OTM put: S=110, K=100
        put_price = self.model.black_scholes_put(110, 100, 1.0, 0.05, 0.2)
        
        # OTM put should have only time value
        self.assertGreater(put_price, 0,
                          msg="OTM put should have positive time value")
        self.assertLess(put_price, 5,
                       msg="OTM put should have reasonable time value")
    
    def test_black_scholes_zero_time(self):
        """Test option pricing at expiration (T=0)"""
        # At expiration, option should equal intrinsic value
        call_price = self.model.black_scholes_call(110, 100, 0, 0.05, 0.2)
        put_price = self.model.black_scholes_put(90, 100, 0, 0.05, 0.2)
        
        self.assertEqual(call_price, 10, msg="Call at expiration should equal intrinsic value")
        self.assertEqual(put_price, 10, msg="Put at expiration should equal intrinsic value")
    
    def test_black_scholes_zero_volatility(self):
        """Test option pricing with zero volatility"""
        # With zero volatility, option should approach intrinsic value discounted
        call_price = self.model.black_scholes_call(100, 100, 1.0, 0.05, 0.0)
        
        # Should be close to max(S*e^(-qT) - K*e^(-rT), 0)
        expected = max(100 - 100 * np.exp(-0.05 * 1.0), 0)
        self.assertAlmostEqual(call_price, expected, places=4,
                              msg="Zero volatility call should equal discounted intrinsic value")
    
    def test_binomial_tree_american_call(self):
        """Test binomial tree pricing for American call"""
        # American call on non-dividend stock should equal European call
        american_price = self.model.binomial_tree_american(100, 100, 1.0, 0.05, 0.2, 100, 'call')
        european_price = self.model.black_scholes_call(100, 100, 1.0, 0.05, 0.2)
        
        # Should be very close (within 0.1 due to discretization)
        self.assertAlmostEqual(american_price, european_price, delta=0.1,
                              msg="American call should approximate European call")
    
    def test_binomial_tree_american_put(self):
        """Test binomial tree pricing for American put"""
        # Deep ITM American put should be worth more than European put
        american_price = self.model.binomial_tree_american(80, 100, 1.0, 0.05, 0.2, 100, 'put')
        european_price = self.model.black_scholes_put(80, 100, 1.0, 0.05, 0.2)
        
        self.assertGreaterEqual(american_price, european_price,
                               msg="American put should be worth at least as much as European put")
    
    def test_greeks_calculation(self):
        """Test Greeks calculations"""
        greeks = self.model.calculate_greeks(100, 100, 1.0, 0.05, 0.2, 'call')
        
        # Test reasonable ranges for Greeks
        self.assertGreater(greeks.delta, 0, msg="Call delta should be positive")
        self.assertLess(greeks.delta, 1, msg="Call delta should be less than 1")
        self.assertGreater(greeks.gamma, 0, msg="Gamma should be positive")
        self.assertLess(greeks.theta, 0, msg="Call theta should be negative (time decay)")
        self.assertGreater(greeks.vega, 0, msg="Vega should be positive")
        self.assertGreater(greeks.rho, 0, msg="Call rho should be positive")
    
    def test_greeks_put_vs_call(self):
        """Test Greeks relationships between puts and calls"""
        call_greeks = self.model.calculate_greeks(100, 100, 1.0, 0.05, 0.2, 'call')
        put_greeks = self.model.calculate_greeks(100, 100, 1.0, 0.05, 0.2, 'put')
        
        # Delta relationship: put_delta = call_delta - 1 (for no dividends)
        expected_put_delta = call_greeks.delta - 1
        self.assertAlmostEqual(put_greeks.delta, expected_put_delta, places=4,
                              msg="Put-call delta relationship should hold")
        
        # Gamma should be the same
        self.assertAlmostEqual(call_greeks.gamma, put_greeks.gamma, places=4,
                              msg="Put and call gamma should be equal")
        
        # Vega should be the same
        self.assertAlmostEqual(call_greeks.vega, put_greeks.vega, places=4,
                              msg="Put and call vega should be equal")
    
    def test_implied_volatility_calculation(self):
        """Test implied volatility calculation"""
        # Calculate theoretical price, then recover volatility
        original_vol = 0.25
        theoretical_price = self.model.black_scholes_call(100, 100, 1.0, 0.05, original_vol)
        
        # Recover implied volatility
        implied_vol = self.model.implied_volatility(theoretical_price, 100, 100, 1.0, 0.05, 'call')
        
        self.assertAlmostEqual(implied_vol, original_vol, places=3,
                              msg="Implied volatility should match original volatility")
    
    def test_implied_volatility_edge_cases(self):
        """Test implied volatility edge cases"""
        # Zero time should return 0
        iv_zero_time = self.model.implied_volatility(10, 100, 100, 0, 0.05, 'call')
        self.assertEqual(iv_zero_time, 0, msg="Zero time should return zero IV")
        
        # Zero price should return 0
        iv_zero_price = self.model.implied_volatility(0, 100, 100, 1.0, 0.05, 'call')
        self.assertEqual(iv_zero_price, 0, msg="Zero price should return zero IV")
    
    def test_put_call_parity(self):
        """Test put-call parity relationship"""
        S, K, T, r = 100, 100, 1.0, 0.05
        
        call_price = self.model.black_scholes_call(S, K, T, r, 0.2)
        put_price = self.model.black_scholes_put(S, K, T, r, 0.2)
        
        parity_holds = self.model.put_call_parity_check(call_price, put_price, S, K, T, r)
        self.assertTrue(parity_holds, msg="Put-call parity should hold for European options")
    
    def test_dividend_adjustment(self):
        """Test dividend-adjusted pricing"""
        # Option with dividend should be worth less (call) or more (put)
        call_no_div = self.model.black_scholes_call(100, 100, 1.0, 0.05, 0.2, 0.0)
        call_with_div = self.model.black_scholes_call(100, 100, 1.0, 0.05, 0.2, 0.03)
        
        put_no_div = self.model.black_scholes_put(100, 100, 1.0, 0.05, 0.2, 0.0)
        put_with_div = self.model.black_scholes_put(100, 100, 1.0, 0.05, 0.2, 0.03)
        
        self.assertLess(call_with_div, call_no_div, 
                       msg="Call with dividend should be worth less")
        self.assertGreater(put_with_div, put_no_div,
                          msg="Put with dividend should be worth more")
    
    def test_quick_functions(self):
        """Test convenience functions"""
        # Test quick Black-Scholes
        quick_price = quick_black_scholes(100, 100, 1.0, 0.05, 0.2, 'call')
        regular_price = self.model.black_scholes_call(100, 100, 1.0, 0.05, 0.2)
        
        self.assertEqual(quick_price, regular_price,
                        msg="Quick function should match regular function")
        
        # Test quick Greeks
        quick_greeks_result = quick_greeks(100, 100, 1.0, 0.05, 0.2, 'call')
        regular_greeks = self.model.calculate_greeks(100, 100, 1.0, 0.05, 0.2, 'call')
        
        self.assertEqual(quick_greeks_result.delta, regular_greeks.delta,
                        msg="Quick Greeks should match regular Greeks")
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Negative stock price should not crash
        result = self.model.black_scholes_call(-100, 100, 1.0, 0.05, 0.2)
        self.assertGreaterEqual(result, 0, msg="Should handle negative stock price gracefully")
        
        # Negative strike should not crash
        result = self.model.black_scholes_call(100, -100, 1.0, 0.05, 0.2)
        self.assertGreaterEqual(result, 0, msg="Should handle negative strike gracefully")
        
        # Negative volatility should not crash
        result = self.model.black_scholes_call(100, 100, 1.0, 0.05, -0.2)
        self.assertGreaterEqual(result, 0, msg="Should handle negative volatility gracefully")

class TestGreeksDataclass(unittest.TestCase):
    """Test Greeks dataclass functionality"""
    
    def test_greeks_creation(self):
        """Test Greeks object creation"""
        greeks = Greeks(0.5, 0.02, -0.05, 0.15, 0.10)
        
        self.assertEqual(greeks.delta, 0.5)
        self.assertEqual(greeks.gamma, 0.02)
        self.assertEqual(greeks.theta, -0.05)
        self.assertEqual(greeks.vega, 0.15)
        self.assertEqual(greeks.rho, 0.10)

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
