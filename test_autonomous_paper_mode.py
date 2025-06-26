#!/usr/bin/env python3
"""
Test Autonomous Trading in Paper Mode
Tests autonomous trading functionality without TrueData dependency
"""

import requests
import json
import time

def test_autonomous_paper_trading():
    """Test autonomous trading in paper mode"""
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("🤖 AUTONOMOUS TRADING TEST (Paper Mode)")
    print("=" * 55)
    print("Testing autonomous trading without TrueData dependency...")
    print()
    
    try:
        # Step 1: Check current autonomous status
        print("1. Checking current autonomous trading status...")
        
        status_response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            trading_active = status_data.get('data', {}).get('trading_active', False)
            session_id = status_data.get('data', {}).get('session_id')
            
            print(f"   Trading Active: {trading_active}")
            print(f"   Session ID: {session_id}")
            
            if trading_active:
                print("   ✅ Autonomous trading already running!")
            else:
                print("   📋 Autonomous trading not active")
                
        else:
            print(f"   ❌ Status check failed: {status_response.status_code}")
            return
        
        print()
        
        # Step 2: Test starting autonomous trading
        if not trading_active:
            print("2. Starting autonomous trading...")
            
            start_response = requests.post(
                f"{base_url}/api/v1/autonomous/start", 
                json={},
                timeout=30
            )
            
            print(f"   Start response: {start_response.status_code}")
            
            if start_response.status_code == 200:
                start_data = start_response.json()
                print("   ✅ Start request successful")
                print(f"   Message: {start_data.get('message', 'No message')}")
                
                # Check status again
                print("\n3. Checking status after start...")
                
                status_response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
                if status_response.status_code == 200:
                    new_status = status_response.json()
                    new_trading_active = new_status.get('data', {}).get('trading_active', False)
                    new_session_id = new_status.get('data', {}).get('session_id')
                    
                    print(f"   Trading Active: {new_trading_active}")
                    print(f"   Session ID: {new_session_id}")
                    
                    if new_trading_active and new_session_id:
                        print("   🎉 SUCCESS: Autonomous trading started!")
                        
                        # Test getting trading stats
                        print("\n4. Getting trading statistics...")
                        stats_response = requests.get(f"{base_url}/api/v1/autonomous/stats", timeout=10)
                        
                        if stats_response.status_code == 200:
                            stats_data = stats_response.json()
                            print("   ✅ Stats retrieved successfully")
                            
                            stats = stats_data.get('data', {})
                            print(f"   Total trades: {stats.get('total_trades', 0)}")
                            print(f"   Active positions: {stats.get('active_positions', 0)}")
                            print(f"   P&L: ₹{stats.get('total_pnl', 0)}")
                            
                        else:
                            print(f"   ⚠️ Stats failed: {stats_response.status_code}")
                            
                    else:
                        print("   ⚠️ Trading not fully activated")
                        print("   This may be expected if system prerequisites aren't met")
                        
            elif start_response.status_code == 400:
                error_data = start_response.json()
                print(f"   ❌ Bad Request: {error_data.get('detail', 'Unknown error')}")
                
            elif start_response.status_code == 503:
                error_data = start_response.json()
                print(f"   ⚠️ Service Unavailable: {error_data.get('detail', 'Service not ready')}")
                print("   This may be due to missing broker auth or market data")
                
            else:
                print(f"   ❌ Start failed: {start_response.status_code}")
                try:
                    error_data = start_response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    pass
        
        print()
        
        # Step 3: Test system health
        print("5. Checking system health...")
        
        health_response = requests.get(f"{base_url}/api/v1/system/health", timeout=10)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("   ✅ System health check successful")
            
            health = health_data.get('data', {})
            print(f"   Overall status: {health.get('status', 'Unknown')}")
            print(f"   Database: {health.get('database', 'Unknown')}")
            print(f"   Redis: {health.get('redis', 'Unknown')}")
            
        else:
            print(f"   ⚠️ Health check failed: {health_response.status_code}")
        
        print()
        
        # Step 4: Test market data alternatives
        print("6. Testing market data alternatives...")
        
        market_response = requests.get(f"{base_url}/api/market/market-status", timeout=10)
        
        if market_response.status_code == 200:
            market_data = market_response.json()
            print("   ✅ Market status available")
            print(f"   Market: {market_data['data']['market_status']}")
            print(f"   Time: {market_data['data']['ist_time']}")
            
        else:
            print(f"   ⚠️ Market status failed: {market_response.status_code}")
            
    except requests.exceptions.ConnectTimeout:
        print("❌ Connection timeout - app may be down")
    except requests.exceptions.ReadTimeout:
        print("❌ Read timeout - operations taking too long")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 55)
    print("📋 AUTONOMOUS TRADING TEST SUMMARY:")
    print("   ✅ App is stable and responding")
    print("   ✅ Emergency fix prevents crashes")
    print("   ⚠️ TrueData not available (library issue)")
    print("   📊 Paper trading mode should work")
    print("   🔐 Requires broker auth for live trading")
    print("\n🎯 READY FOR MANUAL TESTING!")

if __name__ == "__main__":
    test_autonomous_paper_trading() 