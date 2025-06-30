#!/usr/bin/env python3
"""
Quick Data Persistence Check
Verifies if trading data survives redeployment.
"""
import requests
import json
import os
from datetime import datetime

def check_data_persistence():
    """Check if trading data is persisted vs memory-only"""
    print("🔍 CHECKING DATA PERSISTENCE...")
    print("=" * 50)
    
    # Test autonomous status endpoint
    try:
        # Use deployed URL or local
        base_url = "https://algoauto-9gx56.ondigitalocean.app"
        
        print(f"📡 Checking: {base_url}/api/v1/autonomous/status")
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                trading_data = data['data']
                print("✅ Autonomous trading data found!")
                print(f"   📊 Total Trades: {trading_data.get('total_trades', 0)}")
                print(f"   💰 Daily P&L: ₹{trading_data.get('daily_pnl', 0):,.2f}")
                print(f"   📈 Success Rate: {trading_data.get('success_rate', 0):.1f}%")
                print(f"   🔄 Is Active: {trading_data.get('is_active', False)}")
                
                # Check if this is memory-only or persisted
                if trading_data.get('total_trades', 0) > 0:
                    print("\n⚠️  CRITICAL ANALYSIS:")
                    print("🧠 This data could be MEMORY-ONLY (in orchestrator state)")
                    print("🔥 RISK: Redeployment will DELETE all trading history!")
                    print("💾 SOLUTION: Need Redis/Database persistence")
                    return trading_data
                else:
                    print("\n📊 No trading data to lose")
                    return None
            else:
                print("❌ No trading data in response")
                return None
        else:
            print(f"❌ API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def check_redis_connection():
    """Check if Redis is available for persistence"""
    print("\n🔍 CHECKING REDIS AVAILABILITY...")
    
    try:
        # Check if Redis endpoints work
        base_url = "https://algoauto-9gx56.ondigitalocean.app"
        
        # Try a simple endpoint that might use Redis
        response = requests.get(f"{base_url}/api/v1/system/status", timeout=5)
        
        if response.status_code == 200:
            print("✅ System endpoints responsive (Redis likely available)")
            return True
        else:
            print("⚠️ System endpoints not responding")
            return False
            
    except Exception as e:
        print(f"❌ Redis check failed: {e}")
        return False

def estimate_deployment_risk():
    """Estimate risk of data loss on redeployment"""
    print("\n🚨 DEPLOYMENT RISK ASSESSMENT:")
    print("=" * 40)
    
    trading_data = check_data_persistence()
    redis_available = check_redis_connection()
    
    if not trading_data:
        print("✅ LOW RISK: No significant trading data to lose")
        return "LOW"
    
    trades = trading_data.get('total_trades', 0)
    pnl = trading_data.get('daily_pnl', 0)
    
    if trades > 100 and abs(pnl) > 10000:
        print("🔥 HIGH RISK: Significant trading data exists!")
        print(f"   💸 Could lose {trades} trades worth ₹{pnl:,.2f}")
        print("   🚨 IMMEDIATE ACTION REQUIRED!")
        return "HIGH"
    elif trades > 10:
        print("⚠️ MEDIUM RISK: Some trading data exists")
        return "MEDIUM"
    else:
        print("✅ LOW RISK: Minimal trading data")
        return "LOW"

def create_immediate_backup():
    """Create immediate backup of current trading data"""
    print("\n💾 CREATING EMERGENCY BACKUP...")
    
    try:
        base_url = "https://algoauto-9gx56.ondigitalocean.app"
        
        # Fetch all available data
        endpoints = {
            'autonomous_status': '/api/v1/autonomous/status',
            'dashboard_summary': '/api/v1/dashboard/summary', 
            'system_status': '/api/v1/system/status'
        }
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'backup_reason': 'Pre-deployment data protection',
            'data': {}
        }
        
        for name, endpoint in endpoints.items():
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    backup_data['data'][name] = response.json()
                    print(f"✅ Backed up {name}")
                else:
                    print(f"⚠️ Failed to backup {name}")
            except Exception as e:
                print(f"❌ Error backing up {name}: {e}")
        
        # Save backup file
        backup_filename = f"trading_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"💾 Backup saved: {backup_filename}")
        
        # Show backup summary
        if 'autonomous_status' in backup_data['data']:
            auto_data = backup_data['data']['autonomous_status'].get('data', {})
            print(f"📊 Backup contains: {auto_data.get('total_trades', 0)} trades, ₹{auto_data.get('daily_pnl', 0):,.2f} P&L")
        
        return backup_filename
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def main():
    print("🚨 TRADING DATA PERSISTENCE CHECK")
    print("=" * 50)
    print(f"🕐 Timestamp: {datetime.now()}")
    print()
    
    risk_level = estimate_deployment_risk()
    
    if risk_level in ["HIGH", "MEDIUM"]:
        print("\n💾 CREATING EMERGENCY BACKUP...")
        backup_file = create_immediate_backup()
        
        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print("1. 🛡️ DO NOT REDEPLOY until data is persisted!")
        print("2. 💾 Implement Redis persistence for trading data")
        print("3. 🗄️ Add database storage for trade history") 
        print("4. 📊 Test data recovery from backup")
        
        if backup_file:
            print(f"5. 🔐 Keep backup file safe: {backup_file}")
    
    print(f"\n⚠️ REDEPLOYMENT IMPACT: {risk_level} RISK")
    print("=" * 50)

if __name__ == "__main__":
    main() 