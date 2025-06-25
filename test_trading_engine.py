#!/usr/bin/env python3
"""
Test Trading Engine - Check why autonomous trading hasn't started
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_endpoint(endpoint, method="GET", data=None, description=""):
    """Test an API endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🔍 Testing: {description or endpoint}")
        
        if method == "GET":
            response = requests.get(url, timeout=15)
        elif method == "POST":
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=15)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if isinstance(result, dict) and len(str(result)) < 500:
                    print(f"   Response: {json.dumps(result, indent=4)}")
                else:
                    print(f"   Response: Success (large data)")
                return result
            except:
                print(f"   Response: {response.text[:200]}")
                return response.text
        else:
            print(f"   Error: {response.text[:300]}")
            return None
            
    except Exception as e:
        print(f"   Exception: {str(e)}")
        return None

def check_trading_prerequisites():
    """Check all prerequisites for autonomous trading"""
    print("🔍 CHECKING TRADING PREREQUISITES")
    print("=" * 60)
    
    prerequisites = {}
    
    # 1. Check market data
    print("\n📊 1. MARKET DATA CHECK")
    market_data = test_endpoint("/api/market/indices", description="Market Data")
    if market_data and market_data.get('success'):
        indices = market_data.get('data', {}).get('indices', [])
        live_count = len([idx for idx in indices if idx.get('status') == 'LIVE' and idx.get('last_price', 0) > 0])
        prerequisites['market_data'] = live_count > 0
        print(f"   ✅ Live market data: {live_count} indices with live prices")
    else:
        prerequisites['market_data'] = False
        print("   ❌ No live market data")
    
    # 2. Check TrueData connection
    print("\n🔌 2. TRUEDATA CONNECTION CHECK")
    truedata_status = test_endpoint("/api/v1/truedata/truedata/status", description="TrueData Status")
    if truedata_status and truedata_status.get('success'):
        connected = truedata_status.get('data', {}).get('connected', False)
        symbols = truedata_status.get('data', {}).get('total_symbols', 0)
        prerequisites['truedata'] = connected and symbols > 0
        print(f"   ✅ TrueData connected: {connected}, Symbols: {symbols}")
    else:
        prerequisites['truedata'] = False
        print("   ❌ TrueData not connected")
    
    # 3. Check broker users/accounts
    print("\n🏦 3. BROKER ACCOUNTS CHECK")
    # Try multiple possible endpoints for broker/user info
    broker_endpoints = [
        "/api/v1/users/current",
        "/api/v1/users",
        "/api/v1/control/users",
        "/api/v1/broker/users",
        "/api/v1/zerodha/users"
    ]
    
    broker_found = False
    for endpoint in broker_endpoints:
        result = test_endpoint(endpoint, description=f"Broker Users ({endpoint})")
        if result and isinstance(result, dict):
            if 'users' in result or 'data' in result or 'username' in result:
                prerequisites['broker_users'] = True
                broker_found = True
                print(f"   ✅ Found broker user data at {endpoint}")
                break
    
    if not broker_found:
        prerequisites['broker_users'] = False
        print("   ❌ No broker users found")
    
    # 4. Check autonomous trading endpoints
    print("\n🤖 4. AUTONOMOUS TRADING ENDPOINTS CHECK")
    autonomous_endpoints = [
        "/api/v1/control/autonomous/status",
        "/api/v1/autonomous/status", 
        "/api/v1/trading/autonomous/status",
        "/api/v1/control/status"
    ]
    
    autonomous_found = False
    for endpoint in autonomous_endpoints:
        result = test_endpoint(endpoint, description=f"Autonomous Status ({endpoint})")
        if result and isinstance(result, dict):
            autonomous_found = True
            prerequisites['autonomous_api'] = True
            print(f"   ✅ Found autonomous trading API at {endpoint}")
            
            # Check if trading is enabled/running
            if 'running' in result or 'enabled' in result or 'status' in result:
                status = result.get('running', result.get('enabled', result.get('status', 'unknown')))
                print(f"   📊 Trading Status: {status}")
            break
    
    if not autonomous_found:
        prerequisites['autonomous_api'] = False
        print("   ❌ No autonomous trading API found")
    
    # 5. Check database health
    print("\n💾 5. DATABASE CHECK")
    db_endpoints = [
        "/api/v1/database/health",
        "/api/v1/db-health",
        "/api/v1/health/database"
    ]
    
    db_found = False
    for endpoint in db_endpoints:
        result = test_endpoint(endpoint, description=f"Database Health ({endpoint})")
        if result and isinstance(result, dict):
            prerequisites['database'] = True
            db_found = True
            print(f"   ✅ Database accessible at {endpoint}")
            break
    
    if not db_found:
        prerequisites['database'] = False
        print("   ❌ Database health check not available")
    
    return prerequisites

def check_trading_engine_status():
    """Try to find and check the trading engine status"""
    print("\n🚀 TRADING ENGINE STATUS CHECK")
    print("=" * 60)
    
    # Try to start autonomous trading
    start_endpoints = [
        "/api/v1/control/autonomous/start",
        "/api/v1/autonomous/start",
        "/api/v1/trading/start"
    ]
    
    for endpoint in start_endpoints:
        print(f"\n🔄 Attempting to start trading via {endpoint}")
        result = test_endpoint(endpoint, method="POST", description="Start Trading")
        if result:
            print(f"   📊 Start result: {result}")

def main():
    """Main trading engine diagnostic"""
    print("🚀 AUTONOMOUS TRADING ENGINE DIAGNOSTIC")
    print("=" * 70)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check prerequisites
    prerequisites = check_trading_prerequisites()
    
    # Check trading engine
    check_trading_engine_status()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 70)
    
    total_checks = len(prerequisites)
    passed_checks = sum(prerequisites.values())
    
    print(f"✅ Prerequisites Passed: {passed_checks}/{total_checks}")
    
    for check, status in prerequisites.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {check.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
    
    if passed_checks == total_checks:
        print("\n🎉 ALL PREREQUISITES MET - Trading should be possible!")
        print("💡 If trading isn't starting, check:")
        print("   1. Trading engine configuration")
        print("   2. Risk management settings")
        print("   3. Capital allocation")
        print("   4. Strategy selection")
    elif passed_checks >= 3:
        print("\n⚠️ MOST PREREQUISITES MET - Some issues to resolve")
    else:
        print("\n❌ CRITICAL ISSUES - Multiple prerequisites failing")

if __name__ == "__main__":
    main() 