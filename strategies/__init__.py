# INSTITUTIONAL-GRADE TRADING STRATEGIES
# Professional strategies with advanced mathematical models

from .momentum_surfer import EnhancedMomentumSurfer
from .news_impact_scalper import EnhancedNewsImpactScalper
from .optimized_volume_scalper import OptimizedVolumeScalper
from .regime_adaptive_controller import RegimeAdaptiveController

# EnhancedVolatilityExplosion disabled due to duplication with OptimizedVolumeScalper

__all__ = [
    "EnhancedMomentumSurfer",
    "EnhancedNewsImpactScalper",
    "OptimizedVolumeScalper",
    "RegimeAdaptiveController"
]