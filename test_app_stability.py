#!/usr/bin/env python3
"""
App Stability & Functionality Test
Tests all major components after emergency TrueData fix
"""

import requests
import json
import time

def test_app_stability():
    """Test app stability and functionality after TrueData fix"""
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("🚀 APP STABILITY & FUNCTIONALITY TEST")
    print("=" * 60)
    print("Testing after TrueData emergency fix deployment...")
    print()
    
    results = {
        "app_stability": False,
        "auth_endpoints": False,
        "market_data": False,
        "truedata_safe": False,
        "total_score": 0
    }
    
    try:
        # Test 1: App Health & Stability
        print("🏥 TEST 1: App Health & Stability")
        print("-" * 40)
        
        try:
            health_response = requests.get(f"{base_url}/health", timeout=10)
            if health_response.status_code == 200:
                print("✅ Health endpoint: RESPONDING")
                results["app_stability"] = True
                results["total_score"] += 1
            else:
                print(f"⚠️ Health endpoint: {health_response.status_code}")
        except Exception as e:
            print(f"❌ Health endpoint: ERROR - {e}")
        
        try:
            api_response = requests.get(f"{base_url}/api", timeout=10)
            if api_response.status_code == 200:
                api_data = api_response.json()
                print(f"✅ API root: RESPONDING (v{api_data.get('version', 'unknown')})")
            else:
                print(f"⚠️ API root: {api_response.status_code}")
        except Exception as e:
            print(f"❌ API root: ERROR - {e}")
        
        print()
        
        # Test 2: Auth Endpoints (Previously Failing)
        print("🔐 TEST 2: Auth Endpoints (Previously Failing)")
        print("-" * 40)
        
        try:
            auth_response = requests.get(f"{base_url}/auth/zerodha/status", timeout=10)
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                print("✅ Auth status endpoint: WORKING")
                print(f"   Message: {auth_data.get('message', 'No message')}")
                results["auth_endpoints"] = True
                results["total_score"] += 1
            else:
                print(f"❌ Auth status: {auth_response.status_code}")
        except Exception as e:
            print(f"❌ Auth status: ERROR - {e}")
        
        try:
            auth_url_response = requests.get(f"{base_url}/auth/zerodha/auth-url", timeout=10)
            if auth_url_response.status_code == 200:
                print("✅ Auth URL endpoint: WORKING")
            else:
                print(f"⚠️ Auth URL: {auth_url_response.status_code}")
        except Exception as e:
            print(f"❌ Auth URL: ERROR - {e}")
        
        print()
        
        # Test 3: Market Data APIs
        print("📈 TEST 3: Market Data APIs")
        print("-" * 40)
        
        try:
            market_response = requests.get(f"{base_url}/api/market/market-status", timeout=10)
            if market_response.status_code == 200:
                market_data = market_response.json()
                print("✅ Market status: WORKING")
                print(f"   Market: {market_data['data']['market_status']}")
                print(f"   Time: {market_data['data']['ist_time']}")
        except Exception as e:
            print(f"❌ Market status: ERROR - {e}")
        
        try:
            indices_response = requests.get(f"{base_url}/api/market/indices", timeout=10)
            if indices_response.status_code == 200:
                indices_data = indices_response.json()
                indices = indices_data['data']['indices']
                print("✅ Market indices: WORKING")
                
                for idx in indices:
                    symbol = idx['symbol']
                    price = idx['last_price']
                    status = idx['status']
                    print(f"   {symbol}: ₹{price} ({status})")
                
                results["market_data"] = True
                results["total_score"] += 1
            else:
                print(f"❌ Market indices: {indices_response.status_code}")
        except Exception as e:
            print(f"❌ Market indices: ERROR - {e}")
        
        print()
        
        # Test 4: TrueData Status (Should be Disconnected but Safe)
        print("📊 TEST 4: TrueData Status (Should be Safe/Disconnected)")
        print("-" * 40)
        
        try:
            truedata_response = requests.get(f"{base_url}/api/v1/truedata/truedata/status", timeout=10)
            if truedata_response.status_code == 200:
                truedata_data = truedata_response.json()
                connected = truedata_data['data']['connected']
                
                if connected:
                    print("✅ TrueData: CONNECTED (Wow!)")
                    print("   Emergency fix worked AND TrueData is connecting!")
                else:
                    print("✅ TrueData: DISCONNECTED (Safe)")
                    print("   App no longer crashes due to TrueData - SUCCESS!")
                
                results["truedata_safe"] = True
                results["total_score"] += 1
            else:
                print(f"⚠️ TrueData status: {truedata_response.status_code}")
        except Exception as e:
            print(f"❌ TrueData status: ERROR - {e}")
        
        print()
        
        # Test 5: API Routes Discovery
        print("🗂️ TEST 5: API Routes Discovery")
        print("-" * 40)
        
        try:
            routes_response = requests.get(f"{base_url}/api/routes", timeout=10)
            if routes_response.status_code == 200:
                routes_data = routes_response.json()
                total_routes = routes_data.get('total_routes', 0)
                auth_routes = len(routes_data.get('auth_routes', []))
                api_routes = len(routes_data.get('api_routes', []))
                
                print("✅ API routes: WORKING")
                print(f"   Total routes: {total_routes}")
                print(f"   Auth routes: {auth_routes}")
                print(f"   API routes: {api_routes}")
            else:
                print(f"⚠️ API routes: {routes_response.status_code}")
        except Exception as e:
            print(f"❌ API routes: ERROR - {e}")
        
        print()
        
        # Final Assessment
        print("=" * 60)
        print("📋 FINAL ASSESSMENT")
        print("=" * 60)
        
        score_percentage = (results["total_score"] / 4) * 100
        
        if results["app_stability"] and results["auth_endpoints"]:
            print("🎉 SUCCESS: Emergency fix worked!")
            print("✅ App is stable and no longer crashing")
            print("✅ Auth endpoints are working")
            print("✅ Ready for manual testing")
            
            print("\n🧪 NEXT STEPS:")
            print("1. Test the auth modal (🔐 Daily Auth Token button)")
            print("2. Run browser console tests: runAllTests()")
            print("3. Try manual TrueData connection if needed")
            
        elif results["app_stability"]:
            print("⚠️ PARTIAL SUCCESS: App stable but some issues remain")
            print(f"Score: {results['total_score']}/4 ({score_percentage:.0f}%)")
            
        else:
            print("❌ ISSUES REMAIN: App may still have problems")
            print("Need further investigation")
        
        print("=" * 60)
        
        return results
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in testing: {e}")
        return results

if __name__ == "__main__":
    test_app_stability() 