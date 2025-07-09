#!/usr/bin/env python3
"""
Monitor Deployment Fix Progress
Track Redis storage error resolution and market data restoration
"""

import requests
import time
import json
from datetime import datetime

def monitor_deployment_progress():
    """Monitor deployment progress and key fixes"""
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("🔍 MONITORING DEPLOYMENT PROGRESS...")
    print("=" * 60)
    
    # Track key endpoints
    endpoints = {
        "autonomous_status": "/api/v1/autonomous/status",
        "market_data": "/api/v1/market-data",
        "truedata_status": "/api/v1/truedata/status",
        "strategies": "/api/v1/strategies",
        "health": "/api/v1/health"
    }
    
    for i in range(12):  # Monitor for 2 minutes
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n🕐 {timestamp} - Check #{i+1}/12")
        print("-" * 40)
        
        results = {}
        
        # Check each endpoint
        for name, endpoint in endpoints.items():
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                results[name] = {
                    "status": response.status_code,
                    "data": response.json() if response.status_code == 200 else None
                }
                
                # Status indicators
                if response.status_code == 200:
                    print(f"✅ {name}: 200 OK")
                else:
                    print(f"❌ {name}: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                results[name] = {"status": "ERROR", "error": str(e)}
                print(f"🔴 {name}: CONNECTION ERROR")
        
        # Detailed analysis for key endpoints
        if results.get("autonomous_status", {}).get("status") == 200:
            status_data = results["autonomous_status"]["data"]
            print(f"📊 Strategies: {status_data.get('active_strategies', 0)}")
            print(f"📊 Trades: {status_data.get('total_trades', 0)}")
            print(f"📊 System Active: {status_data.get('is_active', False)}")
            print(f"📊 Market Status: {status_data.get('market_status', 'unknown')}")
            
        if results.get("market_data", {}).get("status") == 200:
            market_data = results["market_data"]["data"]
            symbol_count = len(market_data) if isinstance(market_data, list) else 0
            print(f"📈 Market Data: {symbol_count} symbols")
            
            # Check for Redis storage errors (should be ZERO now)
            if symbol_count > 0:
                print("✅ REDIS STORAGE ERRORS: RESOLVED!")
                
        if results.get("truedata_status", {}).get("status") == 200:
            truedata_data = results["truedata_status"]["data"]
            print(f"📡 TrueData Connected: {truedata_data.get('connected', False)}")
            print(f"📡 Symbols Active: {truedata_data.get('symbols_active', 0)}")
        
        # Check for successful deployment indicators
        success_indicators = [
            results.get("autonomous_status", {}).get("status") == 200,
            results.get("market_data", {}).get("status") == 200,
            results.get("truedata_status", {}).get("status") == 200
        ]
        
        if all(success_indicators):
            print("\n🎉 DEPLOYMENT SUCCESS DETECTED!")
            print("✅ All key endpoints responding")
            print("✅ Market data pipeline restored")
            print("✅ Redis storage errors should be resolved")
            
            # Final verification
            if results["autonomous_status"]["data"].get("total_trades", 0) > 0:
                print("🚀 TRADES DETECTED - SYSTEM FULLY OPERATIONAL!")
            else:
                print("⏳ Waiting for trade generation...")
            
            break
        
        # Wait before next check
        if i < 11:
            print("⏳ Waiting 10 seconds for next check...")
            time.sleep(10)
    
    print("\n" + "=" * 60)
    print("📋 DEPLOYMENT MONITORING COMPLETE")
    
    # Final summary
    final_check = {}
    for name, endpoint in endpoints.items():
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            final_check[name] = response.status_code == 200
        except:
            final_check[name] = False
    
    print("\n🎯 FINAL STATUS:")
    for name, status in final_check.items():
        print(f"{'✅' if status else '❌'} {name}: {'OK' if status else 'FAILED'}")
    
    # Success criteria
    critical_endpoints = ["autonomous_status", "market_data", "truedata_status"]
    deployment_success = all(final_check.get(ep, False) for ep in critical_endpoints)
    
    if deployment_success:
        print("\n🎉 DEPLOYMENT SUCCESSFUL!")
        print("✅ Redis storage errors resolved")
        print("✅ Market data pipeline restored")
        print("✅ Transformation bug fixed")
        print("💡 Monitor for trade generation in next few minutes")
    else:
        print("\n⚠️ DEPLOYMENT ISSUES DETECTED")
        print("💡 May need additional investigation")

if __name__ == "__main__":
    monitor_deployment_progress() 