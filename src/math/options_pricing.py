"""
Professional Options Pricing Models
Institutional-grade implementation of Black-Scholes, Binomial Trees, and Greeks calculations
"""

import numpy as np
import scipy.stats as stats
from scipy.optimize import brentq
from typing import Tuple, Optional, Dict
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Greeks:
    """Container for option Greeks"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float

class OptionsPricingModels:
    """
    Professional-grade options pricing models with mathematical accuracy
    
    Features:
    - Black-Scholes-Merton model for European options
    - Binomial tree model for American options
    - Complete Greeks calculations
    - Implied volatility solver
    - Dividend-adjusted pricing
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def black_scholes_call(self, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Black-Scholes call option price with dividend yield
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility (annualized)
            q: Dividend yield (continuous)
            
        Returns:
            Call option price
            
        Example:
            >>> model = OptionsPricingModels()
            >>> price = model.black_scholes_call(100, 100, 1.0, 0.05, 0.2)
            >>> round(price, 2)
            10.45
        """
        try:
            if T <= 0:
                return max(S - K, 0)
            
            if sigma <= 0:
                return max(S * np.exp(-q * T) - K * np.exp(-r * T), 0)
            
            d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            call_price = (S * np.exp(-q * T) * stats.norm.cdf(d1) - 
                         K * np.exp(-r * T) * stats.norm.cdf(d2))
            
            return max(call_price, 0)
            
        except Exception as e:
            self.logger.error(f"Error in Black-Scholes call calculation: {e}")
            return 0.0
    
    def black_scholes_put(self, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Black-Scholes put option price with dividend yield
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility (annualized)
            q: Dividend yield (continuous)
            
        Returns:
            Put option price
        """
        try:
            if T <= 0:
                return max(K - S, 0)
            
            if sigma <= 0:
                return max(K * np.exp(-r * T) - S * np.exp(-q * T), 0)
            
            d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            put_price = (K * np.exp(-r * T) * stats.norm.cdf(-d2) - 
                        S * np.exp(-q * T) * stats.norm.cdf(-d1))
            
            return max(put_price, 0)
            
        except Exception as e:
            self.logger.error(f"Error in Black-Scholes put calculation: {e}")
            return 0.0
    
    def binomial_tree_american(self, S: float, K: float, T: float, r: float, sigma: float, 
                              steps: int, option_type: str = 'call', q: float = 0.0) -> float:
        """
        Binomial tree model for American options
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility (annualized)
            steps: Number of time steps
            option_type: 'call' or 'put'
            q: Dividend yield (continuous)
            
        Returns:
            American option price
        """
        try:
            if T <= 0:
                if option_type.lower() == 'call':
                    return max(S - K, 0)
                else:
                    return max(K - S, 0)
            
            dt = T / steps
            u = np.exp(sigma * np.sqrt(dt))
            d = 1 / u
            p = (np.exp((r - q) * dt) - d) / (u - d)
            
            # Initialize asset prices at maturity
            asset_prices = np.zeros(steps + 1)
            for i in range(steps + 1):
                asset_prices[i] = S * (u ** (steps - i)) * (d ** i)
            
            # Initialize option values at maturity
            option_values = np.zeros(steps + 1)
            for i in range(steps + 1):
                if option_type.lower() == 'call':
                    option_values[i] = max(asset_prices[i] - K, 0)
                else:
                    option_values[i] = max(K - asset_prices[i], 0)
            
            # Backward induction
            for j in range(steps - 1, -1, -1):
                for i in range(j + 1):
                    # European value
                    european_value = np.exp(-r * dt) * (p * option_values[i] + (1 - p) * option_values[i + 1])
                    
                    # Intrinsic value (early exercise)
                    current_price = S * (u ** (j - i)) * (d ** i)
                    if option_type.lower() == 'call':
                        intrinsic_value = max(current_price - K, 0)
                    else:
                        intrinsic_value = max(K - current_price, 0)
                    
                    # American option value is max of European and intrinsic
                    option_values[i] = max(european_value, intrinsic_value)
            
            return option_values[0]
            
        except Exception as e:
            self.logger.error(f"Error in binomial tree calculation: {e}")
            return 0.0
    
    def calculate_greeks(self, S: float, K: float, T: float, r: float, sigma: float, 
                        option_type: str = 'call', q: float = 0.0) -> Greeks:
        """
        Calculate all option Greeks using Black-Scholes model
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility (annualized)
            option_type: 'call' or 'put'
            q: Dividend yield (continuous)
            
        Returns:
            Greeks object with delta, gamma, theta, vega, rho
        """
        try:
            if T <= 0:
                return Greeks(0.0, 0.0, 0.0, 0.0, 0.0)
            
            d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            # Delta
            if option_type.lower() == 'call':
                delta = np.exp(-q * T) * stats.norm.cdf(d1)
            else:
                delta = -np.exp(-q * T) * stats.norm.cdf(-d1)
            
            # Gamma (same for calls and puts)
            gamma = (np.exp(-q * T) * stats.norm.pdf(d1)) / (S * sigma * np.sqrt(T))
            
            # Theta
            theta_part1 = -(S * stats.norm.pdf(d1) * sigma * np.exp(-q * T)) / (2 * np.sqrt(T))
            if option_type.lower() == 'call':
                theta_part2 = r * K * np.exp(-r * T) * stats.norm.cdf(d2)
                theta_part3 = -q * S * np.exp(-q * T) * stats.norm.cdf(d1)
                theta = theta_part1 - theta_part2 + theta_part3
            else:
                theta_part2 = -r * K * np.exp(-r * T) * stats.norm.cdf(-d2)
                theta_part3 = q * S * np.exp(-q * T) * stats.norm.cdf(-d1)
                theta = theta_part1 + theta_part2 + theta_part3
            
            # Convert theta to per-day
            theta = theta / 365.0
            
            # Vega (same for calls and puts)
            vega = S * np.exp(-q * T) * stats.norm.pdf(d1) * np.sqrt(T) / 100.0
            
            # Rho
            if option_type.lower() == 'call':
                rho = K * T * np.exp(-r * T) * stats.norm.cdf(d2) / 100.0
            else:
                rho = -K * T * np.exp(-r * T) * stats.norm.cdf(-d2) / 100.0
            
            return Greeks(delta, gamma, theta, vega, rho)
            
        except Exception as e:
            self.logger.error(f"Error calculating Greeks: {e}")
            return Greeks(0.0, 0.0, 0.0, 0.0, 0.0)
    
    def implied_volatility(self, market_price: float, S: float, K: float, T: float, r: float, 
                          option_type: str = 'call', q: float = 0.0, max_iterations: int = 100) -> float:
        """
        Calculate implied volatility using Brent's method
        
        Args:
            market_price: Observed market price of option
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            option_type: 'call' or 'put'
            q: Dividend yield (continuous)
            max_iterations: Maximum iterations for solver
            
        Returns:
            Implied volatility (annualized)
        """
        try:
            if T <= 0 or market_price <= 0:
                return 0.0
            
            # Define objective function
            def objective(sigma):
                if option_type.lower() == 'call':
                    theoretical_price = self.black_scholes_call(S, K, T, r, sigma, q)
                else:
                    theoretical_price = self.black_scholes_put(S, K, T, r, sigma, q)
                return theoretical_price - market_price
            
            # Check bounds
            if objective(0.001) * objective(5.0) > 0:
                # No solution exists in reasonable range
                return 0.0
            
            # Use Brent's method to find root
            iv = brentq(objective, 0.001, 5.0, maxiter=max_iterations)
            return iv
            
        except Exception as e:
            self.logger.error(f"Error calculating implied volatility: {e}")
            return 0.0
    
    def option_price(self, S: float, K: float, T: float, r: float, sigma: float, 
                    option_type: str = 'call', model: str = 'black_scholes', q: float = 0.0, 
                    steps: int = 100) -> float:
        """
        Unified option pricing interface
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility (annualized)
            option_type: 'call' or 'put'
            model: 'black_scholes' or 'binomial'
            q: Dividend yield (continuous)
            steps: Number of steps for binomial model
            
        Returns:
            Option price
        """
        if model.lower() == 'black_scholes':
            if option_type.lower() == 'call':
                return self.black_scholes_call(S, K, T, r, sigma, q)
            else:
                return self.black_scholes_put(S, K, T, r, sigma, q)
        elif model.lower() == 'binomial':
            return self.binomial_tree_american(S, K, T, r, sigma, steps, option_type, q)
        else:
            raise ValueError(f"Unknown model: {model}")
    
    def put_call_parity_check(self, call_price: float, put_price: float, S: float, K: float, 
                             T: float, r: float, q: float = 0.0, tolerance: float = 0.01) -> bool:
        """
        Verify put-call parity: C - P = S*e^(-qT) - K*e^(-rT)
        
        Args:
            call_price: Call option price
            put_price: Put option price
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            q: Dividend yield (continuous)
            tolerance: Acceptable deviation
            
        Returns:
            True if parity holds within tolerance
        """
        try:
            left_side = call_price - put_price
            right_side = S * np.exp(-q * T) - K * np.exp(-r * T)
            return abs(left_side - right_side) <= tolerance
        except Exception as e:
            self.logger.error(f"Error in put-call parity check: {e}")
            return False

# Convenience functions for quick calculations
def quick_black_scholes(S: float, K: float, T: float, r: float, sigma: float, 
                       option_type: str = 'call') -> float:
    """Quick Black-Scholes calculation without instantiating class"""
    model = OptionsPricingModels()
    return model.option_price(S, K, T, r, sigma, option_type, 'black_scholes')

def quick_greeks(S: float, K: float, T: float, r: float, sigma: float, 
                option_type: str = 'call') -> Greeks:
    """Quick Greeks calculation without instantiating class"""
    model = OptionsPricingModels()
    return model.calculate_greeks(S, K, T, r, sigma, option_type)

def quick_implied_vol(market_price: float, S: float, K: float, T: float, r: float, 
                     option_type: str = 'call') -> float:
    """Quick implied volatility calculation without instantiating class"""
    model = OptionsPricingModels()
    return model.implied_volatility(market_price, S, K, T, r, option_type)

if __name__ == "__main__":
    # Example usage and validation
    model = OptionsPricingModels()
    
    # Test case: S=100, K=100, T=1, r=0.05, sigma=0.2
    call_price = model.black_scholes_call(100, 100, 1.0, 0.05, 0.2)
    put_price = model.black_scholes_put(100, 100, 1.0, 0.05, 0.2)
    
    print(f"Call price: {call_price:.4f}")  # Should be ~10.45
    print(f"Put price: {put_price:.4f}")    # Should be ~5.57
    
    # Test Greeks
    greeks = model.calculate_greeks(100, 100, 1.0, 0.05, 0.2, 'call')
    print(f"Delta: {greeks.delta:.4f}")     # Should be ~0.64
    print(f"Gamma: {greeks.gamma:.4f}")     # Should be ~0.02
    
    # Test put-call parity
    parity_check = model.put_call_parity_check(call_price, put_price, 100, 100, 1.0, 0.05)
    print(f"Put-call parity holds: {parity_check}")
