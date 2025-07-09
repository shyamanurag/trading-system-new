#!/usr/bin/env python3
"""
Comprehensive test of deployed app to verify all fixes are working
Tests: User performance endpoint, trading status, startup bugs, etc.
"""

import asyncio
import sys
import os
import json
sys.path.insert(0, os.path.abspath('.'))

import requests
from datetime import datetime

class DeployedAppTester:
    def __init__(self):
        self.base_url = "https://algoauto-9gx56.ondigitalocean.app"
        self.results = []
        
    def log_test(self, name, success, details, response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            "test": name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data
        })
        print(f"{status} - {name}: {details}")
        
    def test_user_performance_endpoint(self):
        """Test the user performance endpoint that was returning 404"""
        print("\n🔧 Testing User Performance Endpoint Fix...")
        
        try:
            # Test with user_id parameter (the failing case)
            url = f"{self.base_url}/api/v1/users/performance?user_id=MASTER_USER_001"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("user_id") == "MASTER_USER_001":
                    self.log_test(
                        "User Performance Endpoint (with user_id)",
                        True,
                        f"Returns 200 OK with correct user data",
                        data
                    )
                else:
                    self.log_test(
                        "User Performance Endpoint (with user_id)",
                        False,
                        f"Returns 200 but invalid data structure: {data}",
                        data
                    )
            else:
                self.log_test(
                    "User Performance Endpoint (with user_id)",
                    False,
                    f"Returns {response.status_code}: {response.text[:200]}",
                    None
                )
                
            # Test without user_id parameter
            url = f"{self.base_url}/api/v1/users/performance"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "user_metrics" in data.get("data", {}):
                    self.log_test(
                        "User Performance Endpoint (without user_id)",
                        True,
                        f"Returns 200 OK with system performance data",
                        None
                    )
                else:
                    self.log_test(
                        "User Performance Endpoint (without user_id)",
                        False,
                        f"Returns 200 but invalid data structure",
                        None
                    )
            else:
                self.log_test(
                    "User Performance Endpoint (without user_id)",
                    False,
                    f"Returns {response.status_code}: {response.text[:200]}",
                    None
                )
                
        except Exception as e:
            self.log_test(
                "User Performance Endpoint",
                False,
                f"Request failed: {e}",
                None
            )
    
    def test_autonomous_trading_status(self):
        """Test autonomous trading status to check for startup bugs"""
        print("\n🚀 Testing Autonomous Trading System...")
        
        try:
            url = f"{self.base_url}/api/v1/autonomous/status"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    trading_data = data.get("data", {})
                    self.log_test(
                        "Autonomous Trading Status",
                        True,
                        f"Status: {trading_data.get('is_active', 'unknown')}, Strategies: {len(trading_data.get('active_strategies', []))}",
                        {"is_active": trading_data.get("is_active"), "strategies": len(trading_data.get('active_strategies', []))}
                    )
                else:
                    self.log_test(
                        "Autonomous Trading Status",
                        False,
                        f"API returned success=False: {data.get('message', 'no message')}",
                        data
                    )
            else:
                self.log_test(
                    "Autonomous Trading Status",
                    False,
                    f"Returns {response.status_code}: {response.text[:200]}",
                    None
                )
                
        except Exception as e:
            self.log_test(
                "Autonomous Trading Status",
                False,
                f"Request failed: {e}",
                None
            )
    
    def test_orchestrator_status(self):
        """Test orchestrator status to check for initialization bugs"""
        print("\n🎯 Testing Trading Orchestrator...")
        
        try:
            url = f"{self.base_url}/api/v1/orchestrator/status"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    critical_info = data.get("critical_info", {})
                    self.log_test(
                        "Orchestrator Status",
                        True,
                        f"Initialized: {critical_info.get('is_initialized')}, Running: {critical_info.get('is_running')}, Strategies: {critical_info.get('strategies_loaded')}",
                        critical_info
                    )
                else:
                    self.log_test(
                        "Orchestrator Status",
                        False,
                        f"Orchestrator not available: {data.get('message', 'no message')}",
                        data
                    )
            else:
                self.log_test(
                    "Orchestrator Status",
                    False,
                    f"Returns {response.status_code}: {response.text[:200]}",
                    None
                )
                
        except Exception as e:
            self.log_test(
                "Orchestrator Status",
                False,
                f"Request failed: {e}",
                None
            )
    
    def test_market_data_access(self):
        """Test market data access to check cache system"""
        print("\n📊 Testing Market Data System...")
        
        try:
            url = f"{self.base_url}/api/v1/market-data"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    market_data = data.get("data", {})
                    symbols_count = len(market_data.get("data", {})) if isinstance(market_data.get("data"), dict) else 0
                    self.log_test(
                        "Market Data Access",
                        True,
                        f"Connected: {market_data.get('connected', False)}, Symbols: {symbols_count}, Source: {market_data.get('source', 'unknown')}",
                        {"connected": market_data.get("connected"), "symbols": symbols_count, "source": market_data.get("source")}
                    )
                else:
                    self.log_test(
                        "Market Data Access",
                        False,
                        f"API returned success=False: {data.get('message', 'no message')}",
                        data
                    )
            else:
                self.log_test(
                    "Market Data Access",
                    False,
                    f"Returns {response.status_code}: {response.text[:200]}",
                    None
                )
                
        except Exception as e:
            self.log_test(
                "Market Data Access",
                False,
                f"Request failed: {e}",
                None
            )
    
    def test_elite_recommendations(self):
        """Test elite recommendations system"""
        print("\n🎖️ Testing Elite Recommendations...")
        
        try:
            url = f"{self.base_url}/api/v1/elite"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    recommendations = data.get("data", {}).get("recommendations", [])
                    self.log_test(
                        "Elite Recommendations",
                        True,
                        f"Returns {len(recommendations)} recommendations, Status: {data.get('data', {}).get('status', 'unknown')}",
                        {"recommendations_count": len(recommendations)}
                    )
                else:
                    self.log_test(
                        "Elite Recommendations",
                        False,
                        f"API returned success=False: {data.get('message', 'no message')}",
                        data
                    )
            else:
                self.log_test(
                    "Elite Recommendations",
                    False,
                    f"Returns {response.status_code}: {response.text[:200]}",
                    None
                )
                
        except Exception as e:
            self.log_test(
                "Elite Recommendations",
                False,
                f"Request failed: {e}",
                None
            )
    
    def test_health_endpoints(self):
        """Test health endpoints"""
        print("\n🏥 Testing Health Endpoints...")
        
        health_endpoints = [
            ("/health", "Basic Health Check"),
            ("/health/ready/json", "Ready Check"),
            ("/ready", "Readiness Check")
        ]
        
        for endpoint, name in health_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    self.log_test(
                        name,
                        True,
                        f"Returns 200 OK",
                        None
                    )
                else:
                    self.log_test(
                        name,
                        False,
                        f"Returns {response.status_code}",
                        None
                    )
                    
            except Exception as e:
                self.log_test(
                    name,
                    False,
                    f"Request failed: {e}",
                    None
                )
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*70)
        print("🎯 TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - passed
        
        print(f"Total Tests: {len(self.results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%")
        
        if failed > 0:
            print(f"\n🔍 FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['details']}")
        
        print(f"\n⏰ Test completed at: {datetime.now().isoformat()}")
        
        if passed == len(self.results):
            print("🎉 ALL TESTS PASSED! App is working correctly.")
        elif passed >= len(self.results) * 0.8:
            print("✅ Most tests passed. App is mostly functional.")
        else:
            print("⚠️ Multiple failures detected. App needs attention.")
        
        return passed == len(self.results)

async def main():
    """Run all tests"""
    print("🚀 Testing Deployed App - Comprehensive Fix Verification")
    print("="*70)
    print(f"Testing URL: https://algoauto-9gx56.ondigitalocean.app")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("="*70)
    
    tester = DeployedAppTester()
    
    # Run all tests
    tester.test_user_performance_endpoint()
    tester.test_autonomous_trading_status()
    tester.test_orchestrator_status()
    tester.test_market_data_access()
    tester.test_elite_recommendations()
    tester.test_health_endpoints()
    
    # Generate summary
    all_passed = tester.generate_summary()
    
    return all_passed

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1) 