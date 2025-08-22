"""
Professional Mathematical Models for Trading
Institutional-grade implementations of financial mathematics
"""

from .options_pricing import OptionsPricingModels, Greeks, quick_black_scholes, quick_greeks, quick_implied_vol

__all__ = [
    'OptionsPricingModels',
    'Greeks', 
    'quick_black_scholes',
    'quick_greeks',
    'quick_implied_vol'
]
