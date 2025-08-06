# OPTIONS TRADING STRATEGIES
# All strategies updated with new options-focused implementations

from .momentum_surfer import EnhancedMomentumSurfer
from .volatility_explosion import EnhancedVolatilityExplosion
from .news_impact_scalper import EnhancedNewsImpactScalper
from .optimized_volume_scalper import OptimizedVolumeScalper
from .regime_adaptive_controller import RegimeAdaptiveController

__all__ = [
    "EnhancedMomentumSurfer",
    "EnhancedVolatilityExplosion", 
    "EnhancedNewsImpactScalper",
    "OptimizedVolumeScalper",
    "RegimeAdaptiveController"
]