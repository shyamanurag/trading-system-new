#!/usr/bin/env python3
"""
TrueData Connection Recovery Script
Diagnoses and fixes common TrueData connection issues
"""

import sys
import os
import time
import requests
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_truedata_status():
    """Check current TrueData connection status"""
    try:
        # Import TrueData functions
        from data.truedata_client import (
            get_connection_status, 
            get_truedata_status,
            reset_circuit_breaker,
            force_disconnect_truedata,
            initialize_truedata,
            truedata_client
        )
        
        print("🔍 DIAGNOSING TRUEDATA CONNECTION...")
        print("=" * 50)
        
        # Get connection status
        status = get_connection_status()
        detailed_status = truedata_client.get_detailed_status()
        
        print(f"📊 Connection Status:")
        print(f"   Connected: {status.get('connected', False)}")
        print(f"   Circuit Breaker Active: {status.get('circuit_breaker_active', False)}")
        print(f"   Consecutive Failures: {status.get('consecutive_failures', 0)}")
        print(f"   Can Attempt Connection: {status.get('can_attempt_connection', False)}")
        print(f"   Deployment ID: {status.get('deployment_id', 'unknown')}")
        
        if detailed_status:
            print(f"\n📋 Detailed Status:")
            print(f"   Connection Attempts: {detailed_status.get('connection_attempts', 0)}")
            print(f"   Shutdown Requested: {detailed_status.get('shutdown_requested', False)}")
            if detailed_status.get('circuit_breaker_remaining_seconds', 0) > 0:
                print(f"   Circuit Breaker Remaining: {detailed_status.get('circuit_breaker_remaining_seconds', 0)}s")
        
        return status, detailed_status
        
    except Exception as e:
        print(f"❌ Error checking TrueData status: {e}")
        return None, None

def fix_truedata_connection():
    """Attempt to fix TrueData connection issues"""
    try:
        from data.truedata_client import (
            reset_circuit_breaker,
            force_disconnect_truedata,
            initialize_truedata,
            truedata_client
        )
        
        print("\n🔧 APPLYING TRUEDATA FIXES...")
        print("=" * 50)
        
        # Step 1: Force disconnect any existing connections
        print("1️⃣ Force disconnecting existing connections...")
        force_disconnect_result = force_disconnect_truedata()
        print(f"   Result: {'✅ Success' if force_disconnect_result else '❌ Failed'}")
        time.sleep(2)
        
        # Step 2: Reset circuit breaker
        print("2️⃣ Resetting circuit breaker...")
        reset_result = reset_circuit_breaker()
        print(f"   Result: {'✅ Success' if reset_result else '❌ Failed'}")
        time.sleep(1)
        
        # Step 3: Reset connection attempts counter
        print("3️⃣ Resetting connection attempts...")
        truedata_client._connection_attempts = 0
        truedata_client._consecutive_failures = 0
        truedata_client._last_connection_failure = None
        truedata_client._shutdown_requested = False
        print("   Result: ✅ Counters reset")
        
        # Step 4: Attempt fresh connection
        print("4️⃣ Attempting fresh connection...")
        connect_result = initialize_truedata()
        print(f"   Result: {'✅ Connected' if connect_result else '❌ Failed'}")
        
        # Step 5: Wait and verify
        print("5️⃣ Verifying connection...")
        time.sleep(3)
        final_status = truedata_client.get_status()
        print(f"   Connected: {final_status.get('connected', False)}")
        print(f"   Data Flowing: {final_status.get('data_flowing', False)}")
        print(f"   Active Symbols: {final_status.get('symbols_active', 0)}")
        
        return final_status.get('connected', False)
        
    except Exception as e:
        print(f"❌ Error fixing TrueData connection: {e}")
        return False

def main():
    """Main recovery function"""
    print("🚀 TRUEDATA CONNECTION RECOVERY")
    print("=" * 50)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Check current status
    status, detailed = check_truedata_status()
    
    if status and status.get('connected', False):
        print("\n✅ TrueData is already connected!")
        print("   No action needed.")
        return True
    
    # Attempt fixes
    success = fix_truedata_connection()
    
    if success:
        print("\n✅ TRUEDATA CONNECTION RESTORED!")
        print("   Market data should now be flowing.")
    else:
        print("\n❌ TRUEDATA CONNECTION RECOVERY FAILED")
        print("   Possible issues:")
        print("   - Network connectivity to push.truedata.in:8084")
        print("   - TrueData credentials invalid")
        print("   - TrueData server maintenance")
        print("   - Multiple deployments conflict")
        
    return success

if __name__ == "__main__":
    main()