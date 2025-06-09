#!/usr/bin/env python3
"""
Test Local Deployment - Comprehensive functionality test
"""
import requests
import json
import time
import websocket
import threading
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

class LocalDeploymentTester:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
        self.auth_token = None
        
    def log(self, msg, level="INFO"):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")
        
    def test_health_endpoints(self):
        """Test health check endpoints"""
        self.log("Testing health endpoints...")
        
        endpoints = [
            "/",
            "/health",
            "/health/alive",
            "/health/ready"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                self.results["tests"][f"health_{endpoint}"] = {
                    "status": "PASS" if response.status_code == 200 else "FAIL",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
                self.log(f"✅ {endpoint}: {response.status_code}")
            except Exception as e:
                self.results["tests"][f"health_{endpoint}"] = {
                    "status": "FAIL",
                    "error": str(e)
                }
                self.log(f"❌ {endpoint}: {e}", "ERROR")
                
    def test_authentication(self):
        """Test authentication flow"""
        self.log("Testing authentication...")
        
        # Test login
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.results["tests"]["auth_login"] = {
                    "status": "PASS",
                    "has_token": bool(self.auth_token),
                    "user_info": data.get("user", {})
                }
                self.log("✅ Authentication successful")
            else:
                self.results["tests"]["auth_login"] = {
                    "status": "FAIL",
                    "status_code": response.status_code,
                    "response": response.text[:200]
                }
                self.log(f"❌ Authentication failed: {response.status_code}", "ERROR")
                
        except Exception as e:
            self.results["tests"]["auth_login"] = {
                "status": "FAIL",
                "error": str(e)
            }
            self.log(f"❌ Authentication error: {e}", "ERROR")
            
    def test_api_endpoints(self):
        """Test various API endpoints"""
        self.log("Testing API endpoints...")
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        endpoints = [
            ("/api/users", "GET"),
            ("/api/recommendations/elite", "GET"),
            ("/api/performance/elite-trades", "GET"),
            ("/api/performance/daily-pnl", "GET"),
            ("/api/market-data/indices", "GET"),
            ("/api/monitoring/system-status", "GET")
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
                    
                self.results["tests"][f"api_{endpoint}"] = {
                    "status": "PASS" if response.status_code in [200, 201] else "FAIL",
                    "status_code": response.status_code,
                    "has_data": bool(response.json()) if response.status_code == 200 else False
                }
                
                status_icon = "✅" if response.status_code in [200, 201] else "❌"
                self.log(f"{status_icon} {endpoint}: {response.status_code}")
                
            except Exception as e:
                self.results["tests"][f"api_{endpoint}"] = {
                    "status": "FAIL",
                    "error": str(e)
                }
                self.log(f"❌ {endpoint}: {e}", "ERROR")
                
    def test_websocket_connection(self):
        """Test WebSocket connectivity"""
        self.log("Testing WebSocket connection...")
        
        try:
            # Test WebSocket connection
            ws = websocket.WebSocket()
            ws_connected = False
            
            try:
                ws.connect(f"{WS_URL}/test_user")
                ws_connected = True
                
                # Wait for welcome message
                welcome = ws.recv()
                welcome_data = json.loads(welcome)
                
                # Send a test message
                ws.send(json.dumps({
                    "type": "heartbeat"
                }))
                
                # Wait for response
                response = ws.recv()
                
                self.results["tests"]["websocket"] = {
                    "status": "PASS",
                    "connected": True,
                    "welcome_received": bool(welcome_data),
                    "heartbeat_response": bool(response)
                }
                self.log("✅ WebSocket connection successful")
                
            except Exception as e:
                self.results["tests"]["websocket"] = {
                    "status": "FAIL",
                    "connected": ws_connected,
                    "error": str(e)
                }
                self.log(f"❌ WebSocket error: {e}", "ERROR")
            finally:
                ws.close()
                
        except Exception as e:
            self.results["tests"]["websocket"] = {
                "status": "FAIL",
                "error": str(e)
            }
            self.log(f"❌ WebSocket connection failed: {e}", "ERROR")
            
    def test_frontend_availability(self):
        """Test if frontend is accessible"""
        self.log("Testing frontend availability...")
        
        frontend_url = "http://localhost:5173"  # Vite default port
        
        try:
            response = requests.get(frontend_url, timeout=5)
            self.results["tests"]["frontend"] = {
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "is_html": "text/html" in response.headers.get("content-type", "")
            }
            
            if response.status_code == 200:
                self.log("✅ Frontend is accessible")
            else:
                self.log(f"❌ Frontend returned: {response.status_code}", "ERROR")
                
        except Exception as e:
            self.results["tests"]["frontend"] = {
                "status": "FAIL",
                "error": str(e)
            }
            self.log(f"❌ Frontend not accessible: {e}", "ERROR")
            
    def generate_summary(self):
        """Generate test summary"""
        for test_name, result in self.results["tests"].items():
            self.results["summary"]["total"] += 1
            if result.get("status") == "PASS":
                self.results["summary"]["passed"] += 1
            else:
                self.results["summary"]["failed"] += 1
                
        self.results["summary"]["success_rate"] = (
            self.results["summary"]["passed"] / self.results["summary"]["total"] * 100
            if self.results["summary"]["total"] > 0 else 0
        )
        
    def run_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("LOCAL DEPLOYMENT TEST")
        print("="*60 + "\n")
        
        # Wait a bit for services to start
        self.log("Waiting for services to start...")
        time.sleep(3)
        
        # Run tests
        self.test_health_endpoints()
        self.test_authentication()
        self.test_api_endpoints()
        self.test_websocket_connection()
        self.test_frontend_availability()
        
        # Generate summary
        self.generate_summary()
        
        # Save results
        with open("local_deployment_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"\nTotal Tests: {self.results['summary']['total']}")
        print(f"Passed: {self.results['summary']['passed']} ✅")
        print(f"Failed: {self.results['summary']['failed']} ❌")
        print(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        if self.results['summary']['failed'] > 0:
            print("\nFailed Tests:")
            for test_name, result in self.results["tests"].items():
                if result.get("status") == "FAIL":
                    error = result.get("error", "Unknown error")
                    print(f"- {test_name}: {error}")
                    
        print(f"\nDetailed results saved to: local_deployment_test_results.json")
        
        # Return success status
        return self.results['summary']['failed'] == 0

if __name__ == "__main__":
    tester = LocalDeploymentTester()
    success = tester.run_tests()
    exit(0 if success else 1) 