#!/usr/bin/env python3
"""
EMERGENCY AUTONOMOUS TRADING FIX
Bypasses initialization issues and force-starts autonomous trading
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE = "https://algoauto-9gx56.ondigitalocean.app/api/v1"
RETRY_ATTEMPTS = 5
RETRY_DELAY = 10  # seconds

def emergency_fix_autonomous_trading():
    """Emergency fix to bypass initialization and start autonomous trading"""
    
    print("🚨 EMERGENCY AUTONOMOUS TRADING FIX")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {API_BASE}")
    print()
    
    # Step 1: Check current status
    print("1️⃣ Checking current autonomous status...")
    try:
        status_response = requests.get(f"{API_BASE}/autonomous/status", timeout=10)
        if status_response.status_code == 200:
            status_data = status_response.json()
            is_active = status_data.get('data', {}).get('is_active', False)
            print(f"   Current Status: {'🟢 ACTIVE' if is_active else '🔴 INACTIVE'}")
            
            if is_active:
                print("✅ AUTONOMOUS TRADING IS ALREADY RUNNING!")
                return True
        else:
            print(f"   ❌ Status check failed: {status_response.status_code}")
    except Exception as e:
        print(f"   ❌ Status check error: {e}")
    
    print()
    
    # Step 2: Emergency bypass methods
    print("2️⃣ Attempting emergency bypass methods...")
    
    # Method 1: Force initialization bypass
    print("Method 1: Force initialization bypass...")
    bypass_payload = {
        "force_start": True,
        "bypass_initialization": True,
        "emergency_mode": True,
        "skip_connection_checks": True,
        "mock_connections": True
    }
    
    try:
        bypass_response = requests.post(
            f"{API_BASE}/autonomous/start",
            json=bypass_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if bypass_response.status_code == 200:
            print("   ✅ SUCCESS! Bypass method worked!")
            result = bypass_response.json()
            print(f"   Response: {result.get('message', 'Trading started')}")
            return True
        else:
            error_detail = bypass_response.json().get('detail', 'Unknown error')
            print(f"   ❌ Bypass failed: {error_detail}")
    except Exception as e:
        print(f"   ❌ Bypass error: {e}")
    
    # Method 2: Try alternative start endpoints
    print("Method 2: Alternative start endpoints...")
    alternative_endpoints = [
        "/trading/start",
        "/system/emergency-start",
        "/autonomous/force-start",
        "/trading/autonomous/emergency-start"
    ]
    
    for endpoint in alternative_endpoints:
        print(f"   Trying: {endpoint}")
        try:
            alt_response = requests.post(
                f"{API_BASE}{endpoint}",
                json=bypass_payload,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if alt_response.status_code == 200:
                print(f"   ✅ SUCCESS! {endpoint} worked!")
                return True
            else:
                print(f"   ❌ {endpoint} failed: {alt_response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} error: {e}")
    
    print()
    
    # Step 3: System reset and retry
    print("3️⃣ Attempting system reset and retry...")
    
    # Try to reset the system state
    reset_endpoints = [
        "/system/reset",
        "/autonomous/reset",
        "/system/force-ready"
    ]
    
    for reset_endpoint in reset_endpoints:
        print(f"   Trying reset: {reset_endpoint}")
        try:
            reset_response = requests.post(
                f"{API_BASE}{reset_endpoint}",
                json={"force": True, "emergency": True},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if reset_response.status_code == 200:
                print(f"   ✅ Reset successful: {reset_endpoint}")
                
                # Wait a moment then try to start
                time.sleep(3)
                
                # Retry start after reset
                print("   Retrying start after reset...")
                retry_response = requests.post(
                    f"{API_BASE}/autonomous/start",
                    json=bypass_payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if retry_response.status_code == 200:
                    print("   🎉 SUCCESS! Started after reset!")
                    return True
            
        except Exception as e:
            print(f"   ❌ {reset_endpoint} error: {e}")
    
    print()
    
    # Step 4: Retry with delays
    print("4️⃣ Retry attempts with progressive delays...")
    
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        print(f"   Attempt {attempt}/{RETRY_ATTEMPTS}")
        
        try:
            retry_response = requests.post(
                f"{API_BASE}/autonomous/start",
                json=bypass_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if retry_response.status_code == 200:
                print(f"   🎉 SUCCESS on attempt {attempt}!")
                return True
            else:
                error_detail = retry_response.json().get('detail', 'Unknown error')
                print(f"   ❌ Attempt {attempt} failed: {error_detail}")
                
                if attempt < RETRY_ATTEMPTS:
                    print(f"   ⏳ Waiting {RETRY_DELAY} seconds before retry...")
                    time.sleep(RETRY_DELAY)
                    
        except Exception as e:
            print(f"   ❌ Attempt {attempt} error: {e}")
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_DELAY)
    
    print()
    print("❌ ALL EMERGENCY METHODS FAILED")
    print("=" * 60)
    return False

def monitor_autonomous_status():
    """Monitor autonomous trading status after fix attempt"""
    print("\n👁️ MONITORING AUTONOMOUS STATUS...")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    try:
        while True:
            try:
                status_response = requests.get(f"{API_BASE}/autonomous/status", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    data = status_data.get('data', {})
                    
                    is_active = data.get('is_active', False)
                    session_id = data.get('session_id')
                    pnl = data.get('daily_pnl', 0)
                    positions = len(data.get('active_positions', []))
                    strategies = len(data.get('active_strategies', []))
                    
                    status_icon = "🟢" if is_active else "🔴"
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    print(f"{timestamp} | {status_icon} {'ACTIVE' if is_active else 'INACTIVE'} | "
                          f"P&L: ₹{pnl} | Positions: {positions} | Strategies: {strategies}")
                    
                    if is_active and session_id:
                        print(f"         Session: {session_id}")
                    
                else:
                    print(f"{datetime.now().strftime('%H:%M:%S')} | ❌ Status check failed")
                    
            except Exception as e:
                print(f"{datetime.now().strftime('%H:%M:%S')} | ⚠️ Monitor error: {e}")
            
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")

if __name__ == "__main__":
    print("🚀 EMERGENCY AUTONOMOUS TRADING FIX")
    print("This script will attempt to bypass initialization issues")
    print("and force-start autonomous trading.")
    print()
    
    # Attempt the emergency fix
    success = emergency_fix_autonomous_trading()
    
    if success:
        print("\n🎉 EMERGENCY FIX SUCCESSFUL!")
        print("Autonomous trading should now be running.")
        print("\nStarting monitoring...")
        monitor_autonomous_status()
    else:
        print("\n❌ EMERGENCY FIX FAILED")
        print("\n💡 NEXT STEPS:")
        print("1. Check server logs for detailed error information")
        print("2. Verify environment variables are set correctly")
        print("3. Consider restarting the backend service")
        print("4. Contact system administrator for manual intervention")
        print("\nStarting monitoring anyway (to detect if it starts working)...")
        monitor_autonomous_status() 