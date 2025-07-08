#!/usr/bin/env python3
"""
Script to fix the strategies/__init__.py file to include all 6 strategies
"""

content = '''"""
Trading Strategies Package
Contains various trading strategies for the automated trading system
"""

from .momentum_surfer import EnhancedMomentumSurfer
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
'''

with open('strategies/__init__.py', 'w') as f:
    f.write(content)

print("✅ Fixed strategies/__init__.py with all 6 strategies")
print("✅ Now all 6 strategies should load in the orchestrator") 