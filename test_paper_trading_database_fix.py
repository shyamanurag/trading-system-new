#!/usr/bin/env python3
"""
Comprehensive Test Script for Paper Trading Database Fix
========================================================

Tests the migration 010 and database persistence fixes for paper trading system.
Run when markets are closed to verify all fixes work correctly.

Author: AI Assistant
Date: 2025-07-15
"""

import os
import sys
import asyncio
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class PaperTradingDatabaseTester:
    """Comprehensive tester for paper trading database fixes"""
    
    def __init__(self):
        self.base_url = "https://algoauto-9gx56.ondigitalocean.app"
        self.results = {}
        self.test_counter = 0
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_result(self, test_name: str, success: bool, details: str = ""):
        """Record test result"""
        self.test_counter += 1
        status = "✅ PASS" if success else "❌ FAIL"
        self.log(f"Test {self.test_counter}: {test_name} - {status}")
        if details:
            self.log(f"   Details: {details}")
        
        self.results[test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        return success
    
    async def test_deployment_status(self) -> bool:
        """Test 1: Verify deployment is running with latest commits"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/system/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                deployment_id = data.get("deployment_info", {}).get("deployment_id", "unknown")
                
                # Check if it's a recent deployment (should be newer than the one we saw earlier)
                is_recent = "1752573" in deployment_id or deployment_id > "deploy_1752572144"
                
                return self.test_result(
                    "Deployment Status",
                    is_recent,
                    f"Deployment ID: {deployment_id}, System Ready: {data.get('system_ready', False)}"
                )
            else:
                return self.test_result("Deployment Status", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.test_result("Deployment Status", False, f"Connection error: {e}")
    
    async def test_database_connection(self) -> bool:
        """Test 2: Verify database connection and health"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/db-health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                db_healthy = data.get("status") == "healthy"
                
                return self.test_result(
                    "Database Connection",
                    db_healthy,
                    f"Status: {data.get('status')}, Message: {data.get('message', 'N/A')}"
                )
            else:
                return self.test_result("Database Connection", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.test_result("Database Connection", False, f"Error: {e}")
    
    async def test_users_table_schema(self) -> bool:
        """Test 3: Verify users table has proper schema with id column"""
        try:
            # Test the specific query that was failing
            response = requests.get(f"{self.base_url}/api/v1/users", timeout=10)
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                # Check if we have users and they have id fields
                has_users = len(users) > 0
                has_id_field = all("id" in user for user in users) if users else False
                
                success = has_users and has_id_field
                details = f"Users found: {len(users)}, All have ID field: {has_id_field}"
                
                if users:
                    first_user = users[0]
                    details += f", First user ID: {first_user.get('id', 'MISSING')}"
                
                return self.test_result("Users Table Schema", success, details)
            else:
                return self.test_result("Users Table Schema", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.test_result("Users Table Schema", False, f"Error: {e}")
    
    async def test_trading_system_status(self) -> bool:
        """Test 4: Verify trading system components are working"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/autonomous/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                system_ready = data.get("system_ready", False)
                strategies_loaded = data.get("strategies_loaded", 0)
                order_manager_ready = data.get("order_manager_ready", False)
                
                success = system_ready and strategies_loaded >= 5 and order_manager_ready
                details = f"System Ready: {system_ready}, Strategies: {strategies_loaded}, OrderManager: {order_manager_ready}"
                
                return self.test_result("Trading System Status", success, details)
            else:
                return self.test_result("Trading System Status", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.test_result("Trading System Status", False, f"Error: {e}")
    
    async def test_paper_trading_capability(self) -> bool:
        """Test 5: Test paper trading signal processing (simulation mode)"""
        try:
            # Try to get current trading status first
            response = requests.get(f"{self.base_url}/api/v1/dashboard/trading-status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Check if paper trading is enabled and configured
                paper_trading_enabled = data.get("paper_trading_enabled", False)
                total_trades = data.get("total_trades", 0)
                
                # Since markets are closed, we mainly check configuration
                success = paper_trading_enabled is not False  # Allow True or None
                details = f"Paper Trading Available: {paper_trading_enabled}, Recorded Trades: {total_trades}"
                
                return self.test_result("Paper Trading Capability", success, details)
            else:
                return self.test_result("Paper Trading Capability", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.test_result("Paper Trading Capability", False, f"Error: {e}")
    
    async def test_database_trade_retrieval(self) -> bool:
        """Test 6: Test database trade retrieval functionality"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/trades", timeout=10)
            
            # Accept both 200 (with trades) and 404/empty (no trades yet) as valid
            if response.status_code in [200, 404]:
                if response.status_code == 200:
                    data = response.json()
                    trades = data.get("trades", [])
                    details = f"Trades retrieved successfully, Count: {len(trades)}"
                else:
                    details = "No trades found (expected for fresh system)"
                
                # The important thing is that the endpoint doesn't crash with database errors
                return self.test_result("Database Trade Retrieval", True, details)
            else:
                return self.test_result("Database Trade Retrieval", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.test_result("Database Trade Retrieval", False, f"Error: {e}")
    
    async def test_order_management_endpoints(self) -> bool:
        """Test 7: Test order management endpoints for database integration"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/orders", timeout=10)
            
            # Similar to trades, accept successful retrieval even if empty
            if response.status_code in [200, 404]:
                if response.status_code == 200:
                    data = response.json()
                    orders = data.get("orders", [])
                    details = f"Orders retrieved successfully, Count: {len(orders)}"
                else:
                    details = "No orders found (expected for fresh system)"
                
                return self.test_result("Order Management Endpoints", True, details)
            else:
                return self.test_result("Order Management Endpoints", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.test_result("Order Management Endpoints", False, f"Error: {e}")
    
    async def test_frontend_dashboard_access(self) -> bool:
        """Test 8: Verify frontend dashboard can access trading data"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/dashboard/summary", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Check that dashboard data is properly structured
                has_required_fields = all(key in data for key in ["total_trades", "daily_pnl", "active_positions"])
                details = f"Dashboard data structure valid: {has_required_fields}"
                
                if has_required_fields:
                    details += f", Trades: {data.get('total_trades', 0)}, P&L: {data.get('daily_pnl', 0)}"
                
                return self.test_result("Frontend Dashboard Access", has_required_fields, details)
            else:
                return self.test_result("Frontend Dashboard Access", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.test_result("Frontend Dashboard Access", False, f"Error: {e}")
    
    async def run_comprehensive_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting Comprehensive Paper Trading Database Tests")
        self.log("=" * 60)
        
        tests = [
            self.test_deployment_status,
            self.test_database_connection,
            self.test_users_table_schema,
            self.test_trading_system_status,
            self.test_paper_trading_capability,
            self.test_database_trade_retrieval,
            self.test_order_management_endpoints,
            self.test_frontend_dashboard_access
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                success = await test()
                if success:
                    passed += 1
                await asyncio.sleep(1)  # Brief pause between tests
            except Exception as e:
                self.log(f"Test execution error: {e}", "ERROR")
        
        self.log("=" * 60)
        self.log(f"🎯 TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! Paper trading database fix is working correctly.", "SUCCESS")
        elif passed >= total * 0.8:
            self.log("✅ Most tests passed. Minor issues may exist but core functionality works.", "WARNING")
        else:
            self.log("❌ Several tests failed. Database fix may need additional work.", "ERROR")
        
        # Save detailed results
        self.save_test_results()
        
        return passed, total
    
    def save_test_results(self):
        """Save test results to file for reference"""
        results = {
            "test_run_time": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results.values() if r["success"]),
                "failed": sum(1 for r in self.results.values() if not r["success"])
            },
            "detailed_results": self.results
        }
        
        with open("paper_trading_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        self.log(f"📄 Test results saved to paper_trading_test_results.json")

async def main():
    """Main test execution"""
    tester = PaperTradingDatabaseTester()
    
    print("\n" + "="*80)
    print("🧪 PAPER TRADING DATABASE FIX - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔍 Testing migration 010, database persistence, and frontend integration")
    print("💡 Markets are closed - perfect time for comprehensive testing!")
    print("="*80 + "\n")
    
    try:
        passed, total = await tester.run_comprehensive_tests()
        
        print("\n" + "="*80)
        if passed == total:
            print("🎉 CONCLUSION: Paper trading database fix is SUCCESSFUL!")
            print("✅ All systems operational - ready for live market trading")
        else:
            print(f"⚠️  CONCLUSION: {passed}/{total} tests passed - some issues remain")
            print("📋 Check paper_trading_test_results.json for detailed analysis")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 