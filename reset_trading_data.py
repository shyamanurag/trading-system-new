#!/usr/bin/env python3
"""
🧹 RESET TRADING DATA - Eliminate Fake Data Contamination
========================================================

Resets ALL trading data to clean slate for real money futures trading.
"""

import requests
import json
from datetime import datetime

def reset_trading_data():
    """Reset all trading data on the deployed system"""
    
    base_url = 'https://algoauto-9gx56.ondigitalocean.app'
    
    print("🧹 RESETTING TRADING DATA")
    print("=" * 50)
    print("⚠️  Eliminating fake data contamination")
    print("🏦 Preparing for REAL MONEY futures trading")
    print()
    
    try:
        # 1. Stop autonomous trading
        print("1️⃣ Stopping autonomous trading...")
        stop_response = requests.post(f'{base_url}/api/v1/autonomous/stop', timeout=10)
        print(f"   Stop Response: {stop_response.status_code}")
        
        # 2. Check current contaminated data
        print("\n2️⃣ Checking contaminated data...")
        status_response = requests.get(f'{base_url}/api/v1/autonomous/status', timeout=10)
        
        if status_response.status_code == 200:
            data = status_response.json().get('data', {})
            contaminated_pnl = data.get('daily_pnl', 0)
            contaminated_trades = data.get('total_trades', 0)
            
            print(f"   ❌ Fake P&L: ₹{contaminated_pnl:,.2f}")
            print(f"   ❌ Fake Trades: {contaminated_trades}")
            
            if contaminated_pnl == 0 and contaminated_trades == 0:
                print("   ✅ Data already clean!")
                return True
        
        # 3. Force system restart to clear memory state
        print("\n3️⃣ Forcing system restart...")
        
        # Try to trigger a restart/reset
        restart_endpoints = [
            '/api/v1/system/restart',
            '/api/v1/system/reset',
            '/restart',
            '/reset'
        ]
        
        restart_success = False
        for endpoint in restart_endpoints:
            try:
                restart_response = requests.post(f'{base_url}{endpoint}', timeout=30)
                if restart_response.status_code in [200, 202]:
                    print(f"   ✅ Restart triggered via {endpoint}")
                    restart_success = True
                    break
            except:
                continue
        
        if not restart_success:
            print("   ⚠️  No restart endpoint available")
            print("   📋 Manual deployment restart recommended")
        
        # 4. Wait for system to come back online
        if restart_success:
            print("\n4️⃣ Waiting for system restart...")
            import time
            time.sleep(30)  # Wait 30 seconds for restart
        
        # 5. Verify clean state
        print("\n5️⃣ Verifying clean state...")
        verify_response = requests.get(f'{base_url}/api/v1/autonomous/status', timeout=15)
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json().get('data', {})
            final_pnl = verify_data.get('daily_pnl', 0)
            final_trades = verify_data.get('total_trades', 0)
            
            print(f"   P&L: ₹{final_pnl}")
            print(f"   Trades: {final_trades}")
            
            if final_pnl == 0 and final_trades == 0:
                print("\n✅ SUCCESS: Fake data ELIMINATED!")
                print("🏦 System ready for REAL MONEY trading")
                return True
            else:
                print("\n⚠️  Data still contaminated after restart")
                return False
        else:
            print(f"   ❌ Verification failed: {verify_response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Reset failed: {e}")
        return False

def manual_cleanup_instructions():
    """Provide manual cleanup instructions"""
    print("\n📋 MANUAL CLEANUP INSTRUCTIONS")
    print("=" * 50)
    print("If automatic reset failed, perform these steps:")
    print()
    print("1. 🔄 Redeploy the application:")
    print("   - Push any small change to trigger redeployment")
    print("   - DigitalOcean will restart with fresh containers")
    print()
    print("2. 🗄️  Database reset (if persistent):")
    print("   - Access database console")
    print("   - Run: DELETE FROM trades;")
    print("   - Run: DELETE FROM positions;")
    print("   - Run: DELETE FROM daily_pnl;")
    print()
    print("3. ⚡ Redis reset (if using Redis):")
    print("   - Access Redis console")
    print("   - Run: FLUSHDB")
    print()
    print("4. ✅ Verify clean state:")
    print("   - Check /api/v1/autonomous/status")
    print("   - Ensure P&L = 0 and trades = 0")

if __name__ == "__main__":
    print("🚨 TRADING DATA RESET UTILITY")
    print("Eliminates fake data contamination for real money trading")
    print()
    
    success = reset_trading_data()
    
    if not success:
        manual_cleanup_instructions()
    
    print("\n🎯 Next Steps:")
    print("1. Verify P&L = ₹0.00 and trades = 0")
    print("2. Start autonomous trading")
    print("3. Monitor for REAL trades only")
    print("4. 🏦 Trade with confidence - NO MORE MOCKS!") 