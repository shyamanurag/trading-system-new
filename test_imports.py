#!/usr/bin/env python3
"""
Test script to verify import fixes work correctly
"""

def test_core_models_import():
    """Test that core models can be imported"""
    try:
        from src.core.models import Position, OptionType, OrderSide, MarketRegime
        print("✅ Core models imported successfully:")
        print(f"  - Position: {Position}")
        print(f"  - OptionType: {OptionType}")
        print(f"  - OrderSide: {OrderSide}")
        print(f"  - MarketRegime: {MarketRegime}")
        return True
    except ImportError as e:
        print(f"❌ Core models import failed: {e}")
        return False

def test_base_strategy_import():
    """Test that BaseStrategy can be imported (without numpy)"""
    try:
        # Temporarily mock numpy to avoid the environment issue
        import sys
        from unittest.mock import MagicMock
        
        # Mock numpy
        mock_numpy = MagicMock()
        sys.modules['numpy'] = mock_numpy
        
        from src.core.base import BaseStrategy
        print("✅ BaseStrategy imported successfully")
        return True
    except ImportError as e:
        print(f"❌ BaseStrategy import failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️ BaseStrategy import had other issues: {e}")
        return False

def test_models_structure():
    """Test the models package structure"""
    try:
        import src.models
        print("✅ Models package imported successfully")
        print(f"  - Available exports: {src.models.__all__}")
        return True
    except ImportError as e:
        print(f"❌ Models package import failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Import Fixes...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    if test_core_models_import():
        success_count += 1
    
    if test_base_strategy_import():
        success_count += 1
    
    if test_models_structure():
        success_count += 1
    
    print("=" * 50)
    print(f"📊 Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All import tests passed! The fixes are working.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.") 