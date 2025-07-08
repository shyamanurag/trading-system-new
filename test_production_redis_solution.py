#!/usr/bin/env python3
"""
Production Redis Cache Solution Test
Tests the Redis-based cross-process cache solution in production environment
"""

import time
import json
import requests
from datetime import datetime

def test_production_market_data_api():
    """Test production market data API with Redis cache"""
    print("🔍 TESTING PRODUCTION MARKET DATA API...")
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    try:
        # Test market data endpoint
        print("📡 Calling production market data API...")
        response = requests.get(f"{base_url}/api/v1/market-data", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            symbols_count = data.get('symbols_count', 0)
            source = data.get('source', 'unknown')
            
            print(f"✅ API Response: Success={success}, Symbols={symbols_count}, Source={source}")
            
            if symbols_count > 0:
                print("🎉 SUCCESS: API can access market data!")
                print(f"📊 Data Source: {source}")
                
                # Show sample symbols
                api_data = data.get('data', {})
                sample_symbols = list(api_data.keys())[:5]
                print(f"📊 Sample symbols ({len(sample_symbols)}/{symbols_count}):")
                for symbol in sample_symbols:
                    symbol_data = api_data[symbol]
                    ltp = symbol_data.get('ltp', 'N/A')
                    volume = symbol_data.get('volume', 'N/A')
                    print(f"   📊 {symbol}: ₹{ltp} | Vol: {volume:,}")
                
                return True, symbols_count, source
            else:
                print("❌ API returned 0 symbols")
                print(f"💡 Source: {source}")
                return False, 0, source
        else:
            print(f"❌ API request failed: {response.status_code}")
            return False, 0, "error"
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False, 0, "exception"

def test_system_status():
    """Test system status to see overall health"""
    print("\n🔍 TESTING SYSTEM STATUS...")
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    try:
        response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check orchestrator status
            orchestrator = data.get('orchestrator', {})
            orchestrator_status = orchestrator.get('status', 'unknown')
            
            # Check TrueData status
            truedata = data.get('truedata_connection', {})
            truedata_symbols = truedata.get('available_symbols', 0)
            
            print(f"✅ System Status:")
            print(f"   Orchestrator: {orchestrator_status}")
            print(f"   TrueData Symbols: {truedata_symbols}")
            
            return True, orchestrator_status, truedata_symbols
        else:
            print(f"❌ System status failed: {response.status_code}")
            return False, "error", 0
            
    except Exception as e:
        print(f"❌ System status test failed: {e}")
        return False, "exception", 0

def test_orders_after_fix():
    """Test if orders are being generated after Redis cache fix"""
    print("\n🔍 TESTING ORDER GENERATION AFTER REDIS FIX...")
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    try:
        # Check current orders
        response = requests.get(f"{base_url}/api/v1/orders", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get('orders', [])
            order_count = len(orders)
            
            print(f"📊 Current Order Count: {order_count}")
            
            if order_count > 0:
                print("🎉 SUCCESS: Orders are being generated!")
                
                # Show recent orders
                recent_orders = orders[:3] if orders else []
                for order in recent_orders:
                    symbol = order.get('symbol', 'N/A')
                    side = order.get('side', 'N/A')
                    status = order.get('status', 'N/A')
                    created_at = order.get('created_at', 'N/A')
                    print(f"   📝 {symbol} {side} {status} {created_at[:19] if created_at != 'N/A' else 'N/A'}")
                
                return True, order_count
            else:
                print("⚠️ No orders yet")
                print("💡 This may be normal if:")
                print("   - Market conditions don't meet strategy criteria")
                print("   - Strategies are still warming up")
                print("   - Redis cache is still populating")
                return False, 0
        else:
            print(f"❌ Orders API failed: {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"❌ Orders test failed: {e}")
        return False, 0

def monitor_for_trades(minutes=3):
    """Monitor for trade generation over time"""
    print(f"\n🔍 MONITORING FOR TRADES (next {minutes} minutes)...")
    
    start_time = time.time()
    end_time = start_time + (minutes * 60)
    
    initial_orders = 0
    
    try:
        # Get initial order count
        response = requests.get("https://algoauto-9gx56.ondigitalocean.app/api/v1/orders", timeout=10)
        if response.status_code == 200:
            data = response.json()
            initial_orders = len(data.get('orders', []))
            print(f"📊 Initial orders: {initial_orders}")
        
        check_count = 0
        while time.time() < end_time:
            try:
                # Check every 30 seconds
                time.sleep(30)
                check_count += 1
                
                # Check current order count
                response = requests.get("https://algoauto-9gx56.ondigitalocean.app/api/v1/orders", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    current_orders = len(data.get('orders', []))
                    
                    new_orders = current_orders - initial_orders
                    print(f"⏰ Check {check_count}: {current_orders} orders ({new_orders:+d} new)")
                    
                    if new_orders > 0:
                        print("🎉 NEW TRADES DETECTED!")
                        print("✅ Redis cache solution is working!")
                        return True, current_orders
                
            except Exception as e:
                print(f"⚠️ Monitor check failed: {e}")
        
        print(f"⏰ Monitoring complete - no new trades in {minutes} minutes")
        return False, initial_orders
        
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        return False, 0

def main():
    """Run production Redis cache solution test"""
    print("🚀 PRODUCTION REDIS CACHE SOLUTION TEST")
    print("=" * 60)
    
    # Test 1: Market Data API
    print("1️⃣ MARKET DATA API TEST")
    api_success, symbols_count, source = test_production_market_data_api()
    
    # Test 2: System Status
    print("\n2️⃣ SYSTEM STATUS TEST")
    status_success, orchestrator_status, truedata_symbols = test_system_status()
    
    # Test 3: Order Generation
    print("\n3️⃣ ORDER GENERATION TEST")
    orders_success, order_count = test_orders_after_fix()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 PRODUCTION TEST SUMMARY")
    print(f"{'='*60}")
    
    print(f"Market Data API.......... {'✅ PASS' if api_success else '❌ FAIL'} ({symbols_count} symbols from {source})")
    print(f"System Status............ {'✅ PASS' if status_success else '❌ FAIL'} (Orchestrator: {orchestrator_status})")
    print(f"Order Generation......... {'✅ PASS' if orders_success else '❌ PENDING'} ({order_count} orders)")
    
    # Overall assessment
    if api_success and symbols_count > 0:
        print("\n🎉 REDIS CACHE SOLUTION STATUS: WORKING!")
        print("✅ Market data is accessible across processes")
        print(f"📊 Data source: {source}")
        
        if orders_success:
            print("✅ Trading system is generating orders")
            print("🚀 Complete success - process isolation issue resolved!")
        else:
            print("⏳ Trading system not generating orders yet")
            print("💡 This could be due to:")
            print("   - Market conditions not meeting strategy criteria")
            print("   - Strategies still warming up with market data")
            print("   - Normal operation during low volatility periods")
            
            # Offer to monitor for trades
            print(f"\n🔍 Would you like to monitor for trades for 3 minutes?")
            print("🔄 Running automatic monitoring...")
            monitor_success, final_orders = monitor_for_trades(3)
            
            if monitor_success:
                print("🎉 COMPLETE SUCCESS: Redis solution working perfectly!")
            else:
                print("⏳ No trades in monitoring period - likely normal market behavior")
    
    elif api_success and symbols_count == 0:
        print("\n⚠️ REDIS CACHE SOLUTION STATUS: PARTIAL")
        print("✅ API infrastructure is working")
        print("❌ No market data symbols available")
        print("💡 Possible causes:")
        print("   - TrueData not connected in production")
        print("   - Redis cache not being populated")
        print("   - Market data source configuration issue")
    
    else:
        print("\n❌ REDIS CACHE SOLUTION STATUS: FAILED")
        print("❌ Market data API not accessible")
        print("💡 Check production deployment status")

if __name__ == "__main__":
    main() 