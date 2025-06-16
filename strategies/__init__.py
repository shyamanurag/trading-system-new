"""
Trading Strategies Package
Contains various trading strategies for the automated trading system
"""

from .momentum_surfer import EnhancedMomentumSurfer
from .volatility_explosion import EnhancedVolatilityExplosion
from .volume_profile_scalper import EnhancedVolumeProfileScalper
from .news_impact_scalper import EnhancedNewsImpactScalper

__all__ = [
    'EnhancedMomentumSurfer',
    'EnhancedVolatilityExplosion',
    'EnhancedVolumeProfileScalper',
    'EnhancedNewsImpactScalper'
] 