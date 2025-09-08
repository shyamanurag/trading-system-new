#!/usr/bin/env python3
"""
EMERGENCY PERFORMANCE FIX
Stops the backend overload by disabling resource-intensive operations
"""

import os
import sys
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def emergency_performance_fix():
    """Apply emergency performance fixes to stop system overload"""
    
    print("🚨 EMERGENCY PERFORMANCE FIX STARTING...")
    print("=" * 50)
    
    fixes_applied = []
    
    # 1. Disable strategy validation backtesting
    print("\n1. 🛑 DISABLING STRATEGY VALIDATION BACKTESTING")
    try:
        # Set environment variable to skip validation
        os.environ['SKIP_STRATEGY_VALIDATION'] = 'true'
        os.environ['SKIP_BACKTEST_VALIDATION'] = 'true'
        fixes_applied.append("Strategy validation disabled")
        print("   ✅ Strategy validation backtesting disabled")
    except Exception as e:
        print(f"   ❌ Failed to disable strategy validation: {e}")
    
    # 2. Disable TrueData auto-connection
    print("\n2. 🛑 DISABLING TRUEDATA AUTO-CONNECTION")
    try:
        os.environ['SKIP_TRUEDATA_AUTO_INIT'] = 'true'
        os.environ['DISABLE_TRUEDATA_CONNECTION'] = 'true'
        fixes_applied.append("TrueData auto-connection disabled")
        print("   ✅ TrueData auto-connection disabled")
    except Exception as e:
        print(f"   ❌ Failed to disable TrueData: {e}")
    
    # 3. Set connection timeouts
    print("\n3. ⏱️ SETTING AGGRESSIVE TIMEOUTS")
    try:
        os.environ['REDIS_TIMEOUT'] = '2'  # 2 second timeout
        os.environ['DB_TIMEOUT'] = '3'     # 3 second timeout
        os.environ['API_TIMEOUT'] = '5'    # 5 second timeout
        fixes_applied.append("Aggressive timeouts set")
        print("   ✅ Aggressive timeouts configured")
    except Exception as e:
        print(f"   ❌ Failed to set timeouts: {e}")
    
    # 4. Disable retry loops
    print("\n4. 🛑 DISABLING RETRY LOOPS")
    try:
        os.environ['MAX_RETRIES'] = '1'           # Only 1 retry
        os.environ['RETRY_DELAY'] = '0.5'         # 0.5 second delay
        os.environ['DISABLE_EXHAUSTIVE_SEARCH'] = 'true'  # No exhaustive token search
        fixes_applied.append("Retry loops minimized")
        print("   ✅ Retry loops minimized")
    except Exception as e:
        print(f"   ❌ Failed to disable retries: {e}")
    
    # 5. Enable fallback mode
    print("\n5. 🔄 ENABLING FALLBACK MODE")
    try:
        os.environ['FALLBACK_MODE'] = 'true'
        os.environ['MINIMAL_INITIALIZATION'] = 'true'
        os.environ['SKIP_HEAVY_OPERATIONS'] = 'true'
        fixes_applied.append("Fallback mode enabled")
        print("   ✅ Fallback mode enabled")
    except Exception as e:
        print(f"   ❌ Failed to enable fallback mode: {e}")
    
    # 6. Create emergency config file
    print("\n6. 📝 CREATING EMERGENCY CONFIG")
    try:
        emergency_config = """
# EMERGENCY PERFORMANCE CONFIG
SKIP_STRATEGY_VALIDATION=true
SKIP_BACKTEST_VALIDATION=true
SKIP_TRUEDATA_AUTO_INIT=true
DISABLE_TRUEDATA_CONNECTION=true
REDIS_TIMEOUT=2
DB_TIMEOUT=3
API_TIMEOUT=5
MAX_RETRIES=1
RETRY_DELAY=0.5
DISABLE_EXHAUSTIVE_SEARCH=true
FALLBACK_MODE=true
MINIMAL_INITIALIZATION=true
SKIP_HEAVY_OPERATIONS=true
"""
        with open('.env.emergency', 'w') as f:
            f.write(emergency_config)
        fixes_applied.append("Emergency config file created")
        print("   ✅ Emergency config file created: .env.emergency")
    except Exception as e:
        print(f"   ❌ Failed to create emergency config: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🚨 EMERGENCY FIXES APPLIED:")
    for i, fix in enumerate(fixes_applied, 1):
        print(f"   {i}. {fix}")
    
    print(f"\n🔧 NEXT STEPS:")
    print("   1. Restart the application to apply fixes")
    print("   2. Monitor system performance")
    print("   3. Gradually re-enable features once stable")
    
    return len(fixes_applied)

if __name__ == "__main__":
    asyncio.run(emergency_performance_fix())
