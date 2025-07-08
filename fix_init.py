with open('strategies/__init__.py', 'w') as f:
    f.write("""from .momentum_surfer import EnhancedMomentumSurfer
from .volatility_explosion import EnhancedVolatilityExplosion
from .volume_profile_scalper import EnhancedVolumeProfileScalper
from .news_impact_scalper import EnhancedNewsImpactScalper
from .regime_adaptive_controller import RegimeAdaptiveController
from .confluence_amplifier import ConfluenceAmplifier

__all__ = [
    'EnhancedMomentumSurfer',
    'EnhancedVolatilityExplosion',
    'EnhancedVolumeProfileScalper',
    'EnhancedNewsImpactScalper',
    'RegimeAdaptiveController',
    'ConfluenceAmplifier'
]
""")
print("✅ Fixed strategies/__init__.py with all 6 strategies") 