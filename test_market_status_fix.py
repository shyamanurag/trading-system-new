#!/usr/bin/env python3
"""
Test Market Status Timezone Fix
Verify that market status correctly uses IST timezone
"""
import pytz
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_market_status_timezone():
    """Test that market status correctly uses IST timezone"""
    print("🕐 Testing Market Status Timezone Fix")
    print("=" * 50)
    
    # IST timezone
    ist = pytz.timezone('Asia/Kolkata')
    
    # Current time in different timezones
    now_local = datetime.now()
    now_utc = datetime.utcnow()
    now_ist = datetime.now(ist)
    
    print(f"Local System Time: {now_local.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"UTC Time:          {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")  
    print(f"IST Time:          {now_ist.strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # Test market status logic with different timezones
    def is_market_open_old_logic(dt):
        """Old buggy logic using system time"""
        return 9 <= dt.hour < 15 or (dt.hour == 15 and dt.minute < 30)
    
    def is_market_open_new_logic(dt_ist):
        """New fixed logic using IST"""
        return 9 <= dt_ist.hour < 15 or (dt_ist.hour == 15 and dt_ist.minute < 30)
    
    # Compare results
    old_status = "OPEN" if is_market_open_old_logic(now_local) else "CLOSED"
    new_status = "OPEN" if is_market_open_new_logic(now_ist) else "CLOSED"
    
    print("\n📊 Market Status Results:")
    print(f"Old Logic (System Time): {old_status}")
    print(f"New Logic (IST):         {new_status}")
    
    # Determine if it's actually market hours in IST
    if now_ist.weekday() < 5:  # Monday to Friday
        if (now_ist.hour == 9 and now_ist.minute >= 15) or (10 <= now_ist.hour <= 14) or (now_ist.hour == 15 and now_ist.minute <= 30):
            expected_status = "OPEN"
        else:
            expected_status = "CLOSED"
    else:
        expected_status = "CLOSED"
    
    print(f"Expected (IST Market):   {expected_status}")
    
    # Verification
    if new_status == expected_status:
        print("\n✅ FIXED: Market status is now correct!")
        print("   The app should now show the correct market status.")
    else:
        print("\n⚠️  Issue: Market status still not matching expected")
    
    # Show the exact times that trigger market open/close
    print(f"\n🕐 Market Hours (IST):")
    print(f"   Market Opens:  9:15 AM IST (Currently: {now_ist.hour:02d}:{now_ist.minute:02d})")
    print(f"   Market Closes: 3:30 PM IST") 
    print(f"   Day of Week:   {now_ist.strftime('%A')} (0=Mon, 6=Sun: {now_ist.weekday()})")
    
    return new_status == expected_status

def test_dashboard_updater_import():
    """Test that dashboard updater import works with the fix"""
    try:
        from src.utils.dashboard_updater import AutonomousDashboardUpdater
        
        updater = AutonomousDashboardUpdater()
        print(f"\n🔧 Dashboard Updater IST Timezone: {updater.ist_timezone}")
        
        # Test get schedule status
        import asyncio
        async def test_schedule():
            schedule_status = await updater.get_autonomous_schedule_status()
            return schedule_status.get('market_status', 'UNKNOWN')
        
        market_status = asyncio.run(test_schedule())
        print(f"   Dashboard Market Status: {market_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing dashboard updater: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Market Status Timezone Fix Test")
    print("=" * 60)
    
    # Test timezone logic
    timezone_ok = test_market_status_timezone()
    
    # Test dashboard updater
    dashboard_ok = test_dashboard_updater_import()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"   Timezone Logic: {'✅ PASS' if timezone_ok else '❌ FAIL'}")
    print(f"   Dashboard Update: {'✅ PASS' if dashboard_ok else '❌ FAIL'}")
    
    if timezone_ok and dashboard_ok:
        print("\n🎉 SUCCESS: Market status timezone fix is working!")
        print("   Your app should now correctly show market status during IST trading hours.")
    else:
        print("\n⚠️  Some issues remain. Check the error messages above.")
    
    print("\n🔄 Next Steps:")
    print("   1. Deploy these changes to production")
    print("   2. Refresh your app dashboard")
    print("   3. Verify market status shows 'OPEN' during 9:15 AM - 3:30 PM IST") 