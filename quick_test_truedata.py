#!/usr/bin/env python3
"""
Quick TrueData Test Script
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test TrueData import"""
    try:
        from truedata_ws import TD_live, TD_hist
        print("[SUCCESS] TrueData WebSocket package imported successfully")
        return True
    except ImportError:
        try:
            from truedata import TD_live, TD_hist
            print("[SUCCESS] TrueData legacy package imported successfully")
            return True
        except ImportError:
            print("[ERROR] TrueData not installed")
            print("[INFO] Install with: pip install truedata-ws")
            return False

def test_config():
    """Test configuration"""
    try:
        from config.truedata_config import get_config
        config = get_config()
        print("[SUCCESS] Configuration loaded successfully")
        return True
    except ImportError as e:
        print(f"[ERROR] Configuration import failed: {e}")
        return False

def test_provider():
    """Test provider import"""
    try:
        from data.truedata_client import (
            initialize_truedata,
            get_truedata_status, 
            is_connected,
            live_market_data,
            truedata_connection_status
        )
        print("[SUCCESS] TrueData provider imported successfully")
        return True
    except ImportError as e:
        print(f"[ERROR] Provider import failed: {e}")
        return False

if __name__ == "__main__":
    print("Quick TrueData Test")
    print("=" * 30)
    
    import_success = test_import()
    config_success = test_config()
    provider_success = test_provider()
    
    success_count = sum([import_success, config_success, provider_success])
    total_tests = 3
    
    print(f"\nResults: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("[SUCCESS] All tests passed! TrueData is ready to use.")
    else:
        print("[WARNING] Some tests failed. Check the installation.")
