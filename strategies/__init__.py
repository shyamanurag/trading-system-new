"""
Trading Strategies Package
Contains various trading strategies for the automated trading system
"""

from .momentum_surfer import EnhancedMomentumSurfer
from .volatility_explosion import EnhancedVolatilityExplosion

__all__ = ['EnhancedMomentumSurfer', 'EnhancedVolatilityExplosion'] 