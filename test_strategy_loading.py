#!/usr/bin/env python3
"""
Test script to verify strategy loading and identify which strategies fail to import
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_strategy_imports():
    """Test importing all 6 strategies individually"""
    print("🧪 TESTING STRATEGY IMPORTS...")
    
    strategies_to_test = [
        ('momentum_surfer', 'EnhancedMomentumSurfer'),
        ('volatility_explosion', 'EnhancedVolatilityExplosion'),
        ('volume_profile_scalper', 'EnhancedVolumeProfileScalper'),
        ('news_impact_scalper', 'EnhancedNewsImpactScalper'),
        ('regime_adaptive_controller', 'RegimeAdaptiveController'),
        ('confluence_amplifier', 'ConfluenceAmplifier')
    ]
    
    successful_imports = 0
    
    for module_name, class_name in strategies_to_test:
        try:
            print(f"\n📦 Testing import: {module_name}.{class_name}")
            module = __import__(f'strategies.{module_name}', fromlist=[class_name])
            strategy_class = getattr(module, class_name)
            print(f"✅ SUCCESS: {class_name} imported successfully")
            
            # Test instantiation
            try:
                instance = strategy_class({})
                print(f"✅ SUCCESS: {class_name} instantiated successfully")
                successful_imports += 1
            except Exception as e:
                print(f"❌ INSTANTIATION FAILED: {class_name} - {e}")
                
        except Exception as e:
            print(f"❌ IMPORT FAILED: {class_name} - {e}")
    
    print(f"\n📊 RESULTS: {successful_imports}/6 strategies loaded successfully")
    
    if successful_imports < 6:
        print(f"❌ ISSUE CONFIRMED: Only {successful_imports} strategies loading instead of 6")
    else:
        print("✅ ALL 6 STRATEGIES LOADING CORRECTLY")
    
    return successful_imports

if __name__ == "__main__":
    test_strategy_imports() 