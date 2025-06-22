#!/usr/bin/env python3
"""
Comprehensive Test Script for All WebSocket and API Integrations
Tests all endpoints, WebSocket connections, and external integrations
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration
BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"

class IntegrationTester:
    def __init__(self):
        self.results = {
            "api_endpoints": {},
            "websockets": {},
            "external_integrations": {},
            "timestamp": datetime.now().isoformat()
        }
        self.auth_token = None
        
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Comprehensive Integration Tests")
        print("=" * 60)
        
        # 1. Test Health Endpoints
        await self.test_health_endpoints()
        
        # 2. Test Authentication
        await self.test_authentication()
        
        # 3. Test API Endpoints
        await self.test_api_endpoints()
        
        # 4. Test WebSocket Connections
        await self.test_websockets()
        
        # 5. Test External Integrations
        await self.test_external_integrations()
        
        # 6. Generate Report
        self.generate_report()
        
    async def test_health_endpoints(self):
        """Test all health check endpoints"""
        print("\n🏥 Testing Health Endpoints...")
        
        health_endpoints = [
            "/health",
            "/health/ready",
            "/health/live"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in health_endpoints:
                try:
                    async with session.get(f"{BASE_URL}{endpoint}") as resp:
                        status = resp.status
                        data = await resp.json() if resp.status == 200 else None
                        self.results["api_endpoints"][endpoint] = {
                            "status": status,
                            "success": status == 200,
                            "data": data
                        }
                        print(f"  ✅ {endpoint}: {status}")
                except Exception as e:
                    self.results["api_endpoints"][endpoint] = {
                        "status": "error",
                        "success": False,
                        "error": str(e)
                    }
                    print(f"  ❌ {endpoint}: {str(e)}")
    
    async def test_authentication(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication...")
        
        # Test login
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{BASE_URL}/auth/login",
                    json=login_data
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.auth_token = data.get("access_token")
                        print(f"  ✅ Login successful")
                        self.results["api_endpoints"]["/auth/login"] = {
                            "status": 200,
                            "success": True
                        }
                    else:
                        print(f"  ❌ Login failed: {resp.status}")
                        self.results["api_endpoints"]["/auth/login"] = {
                            "status": resp.status,
                            "success": False
                        }
            except Exception as e:
                print(f"  ❌ Login error: {str(e)}")
                self.results["api_endpoints"]["/auth/login"] = {
                    "status": "error",
                    "success": False,
                    "error": str(e)
                }
    
    async def test_api_endpoints(self):
        """Test all API endpoints"""
        print("\n🔌 Testing API Endpoints...")
        
        # Define all endpoints to test
        endpoints = {
            # Market Data
            "/api/market/indices": "GET",
            "/api/market/market-status": "GET",
            "/api/v1/market-data/symbols": "GET",
            
            # TrueData Integration
            "/api/v1/truedata/status": "GET",
            "/api/v1/truedata/symbols": "GET",
            "/api/v1/truedata/options/all-options": "GET",
            
            # User Management
            "/api/v1/users/": "GET",
            "/api/v1/users/current": "GET",
            
            # Trading Control
            "/api/v1/control/status": "GET",
            "/api/v1/control/paper-trading": "GET",
            
            # Autonomous Trading
            "/api/v1/autonomous/status": "GET",
            
            # Monitoring
            "/api/v1/monitoring/system": "GET",
            "/api/v1/monitoring/metrics": "GET",
            
            # Dashboard
            "/api/v1/dashboard/summary": "GET",
            
            # Database Health
            "/api/v1/db-health/check": "GET",
            
            # Error Monitoring
            "/api/v1/errors/recent": "GET",
            
            # Zerodha
            "/zerodha": "GET",
            "/zerodha-multi": "GET"
        }
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        async with aiohttp.ClientSession() as session:
            for endpoint, method in endpoints.items():
                try:
                    if method == "GET":
                        async with session.get(
                            f"{BASE_URL}{endpoint}",
                            headers=headers
                        ) as resp:
                            status = resp.status
                            self.results["api_endpoints"][endpoint] = {
                                "method": method,
                                "status": status,
                                "success": status in [200, 201]
                            }
                            status_icon = "✅" if status in [200, 201] else "⚠️"
                            print(f"  {status_icon} {method} {endpoint}: {status}")
                except Exception as e:
                    self.results["api_endpoints"][endpoint] = {
                        "method": method,
                        "status": "error",
                        "success": False,
                        "error": str(e)
                    }
                    print(f"  ❌ {method} {endpoint}: {str(e)}")
    
    async def test_websockets(self):
        """Test all WebSocket endpoints"""
        print("\n🔄 Testing WebSocket Connections...")
        
        websocket_endpoints = [
            "/ws",  # Main WebSocket
            "/api/v1/truedata/options/stream",  # Options data stream
        ]
        
        for endpoint in websocket_endpoints:
            try:
                uri = f"{WS_BASE_URL}{endpoint}"
                async with websockets.connect(uri) as websocket:
                    # Send test message
                    await websocket.send(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Try to receive response
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=5.0
                        )
                        data = json.loads(response)
                        self.results["websockets"][endpoint] = {
                            "status": "connected",
                            "success": True,
                            "response": data
                        }
                        print(f"  ✅ {endpoint}: Connected")
                    except asyncio.TimeoutError:
                        self.results["websockets"][endpoint] = {
                            "status": "timeout",
                            "success": False
                        }
                        print(f"  ⚠️ {endpoint}: Connected but no response")
                        
            except Exception as e:
                self.results["websockets"][endpoint] = {
                    "status": "error",
                    "success": False,
                    "error": str(e)
                }
                print(f"  ❌ {endpoint}: {str(e)}")
    
    async def test_external_integrations(self):
        """Test external service integrations"""
        print("\n🌐 Testing External Integrations...")
        
        # Test TrueData Connection
        async with aiohttp.ClientSession() as session:
            # Check TrueData status
            try:
                async with session.get(
                    f"{BASE_URL}/api/v1/truedata/status"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        connected = data.get("connected", False)
                        self.results["external_integrations"]["TrueData"] = {
                            "connected": connected,
                            "status": data
                        }
                        status_icon = "✅" if connected else "⚠️"
                        print(f"  {status_icon} TrueData: {'Connected' if connected else 'Not Connected'}")
                    else:
                        self.results["external_integrations"]["TrueData"] = {
                            "connected": False,
                            "error": f"Status code: {resp.status}"
                        }
                        print(f"  ❌ TrueData: API error {resp.status}")
            except Exception as e:
                self.results["external_integrations"]["TrueData"] = {
                    "connected": False,
                    "error": str(e)
                }
                print(f"  ❌ TrueData: {str(e)}")
            
            # Check Zerodha Integration
            try:
                async with session.get(
                    f"{BASE_URL}/api/zerodha/status"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.results["external_integrations"]["Zerodha"] = {
                            "status": "available",
                            "data": data
                        }
                        print(f"  ✅ Zerodha: API Available")
                    else:
                        self.results["external_integrations"]["Zerodha"] = {
                            "status": "not_available",
                            "error": f"Status code: {resp.status}"
                        }
                        print(f"  ⚠️ Zerodha: Status {resp.status}")
            except Exception as e:
                self.results["external_integrations"]["Zerodha"] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"  ❌ Zerodha: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST REPORT")
        print("=" * 60)
        
        # API Endpoints Summary
        api_success = sum(1 for r in self.results["api_endpoints"].values() if r.get("success"))
        api_total = len(self.results["api_endpoints"])
        print(f"\n📡 API Endpoints: {api_success}/{api_total} successful")
        
        # WebSocket Summary
        ws_success = sum(1 for r in self.results["websockets"].values() if r.get("success"))
        ws_total = len(self.results["websockets"])
        print(f"🔄 WebSockets: {ws_success}/{ws_total} connected")
        
        # External Integrations Summary
        print(f"\n🌐 External Integrations:")
        for service, status in self.results["external_integrations"].items():
            if isinstance(status, dict):
                connected = status.get("connected", status.get("status") == "available")
                icon = "✅" if connected else "❌"
                print(f"  {icon} {service}")
        
        # Failed Endpoints
        failed_endpoints = [
            endpoint for endpoint, result in self.results["api_endpoints"].items()
            if not result.get("success")
        ]
        
        if failed_endpoints:
            print(f"\n⚠️ Failed Endpoints ({len(failed_endpoints)}):")
            for endpoint in failed_endpoints:
                result = self.results["api_endpoints"][endpoint]
                print(f"  - {endpoint}: {result.get('status', 'error')}")
        
        # Save detailed report
        report_file = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Overall Status
        all_api_ok = api_success == api_total
        all_ws_ok = ws_success == ws_total
        overall_status = "✅ PASS" if all_api_ok and all_ws_ok else "❌ FAIL"
        print(f"\n🎯 Overall Status: {overall_status}")

async def main():
    """Main test runner"""
    tester = IntegrationTester()
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as resp:
                if resp.status != 200:
                    print("❌ Server is not responding properly")
                    return
    except Exception as e:
        print(f"❌ Server is not running at {BASE_URL}")
        print(f"   Error: {str(e)}")
        print("\n💡 Please start the server with: python main.py")
        return
    
    # Run tests
    await tester.run_all_tests()

if __name__ == "__main__":
    print("🔍 AlgoAuto Trading System - Integration Test Suite")
    print(f"🔗 Testing server at: {BASE_URL}")
    asyncio.run(main()) 