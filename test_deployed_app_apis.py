#!/usr/bin/env python3
"""
Test script for deployed trading system APIs
Tests all critical endpoints and functionality
"""

import requests
import json
import time
from datetime import datetime
import pytz

# Production URL
BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_api_endpoint(endpoint, method="GET", data=None, description=""):
    """Test an API endpoint and return formatted results"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n{'='*60}")
        print(f"Testing: {description or endpoint}")
        print(f"URL: {url}")
        print(f"Method: {method}")
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        try:
            json_data = response.json()
            print(f"Response:")
            print(json.dumps(json_data, indent=2))
            return json_data
        except:
            print(f"Raw Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None

def main():
    print("🚀 TESTING DEPLOYED TRADING SYSTEM APIs")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # Test 1: Market Status
    market_status = test_api_endpoint(
        "/api/market/market-status", 
        description="Market Status API"
    )
    
    # Test 2: Market Indices (the one we just fixed)
    market_indices = test_api_endpoint(
        "/api/market/indices", 
        description="Market Indices API (Recently Fixed)"
    )
    
    # Test 3: TrueData Status
    truedata_status = test_api_endpoint(
        "/api/v1/truedata/truedata/status", 
        description="TrueData Connection Status"
    )
    
    # Test 4: System Health
    system_health = test_api_endpoint(
        "/api/v1/system/health", 
        description="System Health Check"
    )
    
    # Test 5: Database Health
    db_health = test_api_endpoint(
        "/api/v1/database/health", 
        description="Database Health Check"
    )
    
    # Test 6: Available API Routes
    api_routes = test_api_endpoint(
        "/api", 
        description="Available API Routes"
    )
    
    # Test 7: Autonomous Trading Status
    autonomous_status = test_api_endpoint(
        "/api/v1/control/autonomous/status", 
        description="Autonomous Trading Status"
    )
    
    # Summary Report
    print(f"\n{'='*60}")
    print("📊 SUMMARY REPORT")
    print(f"{'='*60}")
    
    # Market Status Summary
    if market_status:
        is_open = market_status.get('data', {}).get('is_open', False)
        current_time = market_status.get('data', {}).get('current_time', 'Unknown')
        print(f"🕐 Market Status: {'OPEN' if is_open else 'CLOSED'} at {current_time}")
    
    # Market Indices Summary
    if market_indices:
        success = market_indices.get('success', False)
        if success:
            indices = market_indices.get('data', {}).get('indices', [])
            print(f"📈 Market Indices: SUCCESS - {len(indices)} indices available")
            for idx in indices:
                symbol = idx.get('symbol', 'Unknown')
                price = idx.get('last_price', 'N/A')
                print(f"   • {symbol}: ₹{price}")
        else:
            message = market_indices.get('message', 'Unknown error')
            print(f"📈 Market Indices: FAILED - {message}")
    
    # TrueData Summary
    if truedata_status:
        connected = truedata_status.get('data', {}).get('connected', False)
        symbols_count = truedata_status.get('data', {}).get('symbols_available', 0)
        live_symbols = truedata_status.get('data', {}).get('live_data_symbols', [])
        print(f"🔌 TrueData: {'CONNECTED' if connected else 'DISCONNECTED'}")
        print(f"   • Symbols Available: {symbols_count}")
        print(f"   • Live Data Symbols: {live_symbols}")
    
    # System Health Summary
    if system_health:
        status = system_health.get('status', 'Unknown')
        print(f"🏥 System Health: {status}")
    
    print(f"\n{'='*60}")
    print("✅ Test Complete!")

if __name__ == "__main__":
    main() 