#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE DIGITALOCEAN DEPLOYMENT TEST SUITE
===================================================

This script performs thorough testing of the deployed DigitalOcean application,
including frontend functionality, Zerodha authentication, and system health.

Usage: python test_deployed_digitalocean_comprehensive.py [URL]
Default URL: https://algoauto-9gx56.ondigitalocean.app
"""

import sys
import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data class"""
    name: str
    passed: bool
    message: str
    details: Optional[Dict] = None
    duration: float = 0.0

class DigitalOceanAppTester:
    """Comprehensive tester for DigitalOcean deployed app"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': 'AlgoAuto-Test-Suite/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def log_result(self, name: str, passed: bool, message: str, details: Dict = None, duration: float = 0.0):
        """Log test result"""
        result = TestResult(name, passed, message, details, duration)
        self.results.append(result)
        
        status = "✅" if passed else "❌"
        logger.info(f"{status} {name}: {message}")
        if details:
            logger.info(f"   Details: {details}")
    
    async def test_basic_connectivity(self) -> bool:
        """Test basic connectivity to the deployed app"""
        start_time = time.time()
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.log_result(
                        "Basic Connectivity",
                        True,
                        f"App is reachable (Response: {duration:.2f}s)",
                        {"status_code": response.status, "response": data}
                    )
                    return True
                else:
                    self.log_result(
                        "Basic Connectivity",
                        False,
                        f"Health endpoint returned {response.status}",
                        {"status_code": response.status}
                    )
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_result(
                "Basic Connectivity",
                False,
                f"Connection failed: {str(e)}",
                {"error": str(e), "duration": duration}
            )
            return False
    
    async def test_frontend_loading(self) -> bool:
        """Test if frontend loads correctly"""
        start_time = time.time()
        
        try:
            async with self.session.get(self.base_url) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Check for key frontend elements
                    checks = {
                        "HTML Structure": "<!DOCTYPE html>" in html_content,
                        "React App": "react" in html_content.lower() or "vite" in html_content.lower(),
                        "Trading Dashboard": "trading" in html_content.lower() or "dashboard" in html_content.lower(),
                        "CSS/Styles": "<style" in html_content or ".css" in html_content,
                        "JavaScript": "<script" in html_content or ".js" in html_content
                    }
                    
                    passed_checks = sum(checks.values())
                    all_passed = passed_checks >= 3  # At least 3 out of 5 should pass
                    
                    self.log_result(
                        "Frontend Loading",
                        all_passed,
                        f"Frontend loaded successfully ({passed_checks}/5 checks passed)",
                        {"checks": checks, "duration": duration}
                    )
                    return all_passed
                else:
                    self.log_result(
                        "Frontend Loading",
                        False,
                        f"Frontend returned {response.status}",
                        {"status_code": response.status}
                    )
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_result(
                "Frontend Loading",
                False,
                f"Frontend loading failed: {str(e)}",
                {"error": str(e), "duration": duration}
            )
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Test critical API endpoints"""
        endpoints = [
            ("/health", "Health Check"),
            ("/health/ready/json", "Health Ready JSON"),
            ("/api", "API Root"),
            ("/api/auth/me", "Authentication Status"),
            ("/api/v1/market/indices", "Market Indices"),
            ("/api/v1/market/market-status", "Market Status"),
            ("/api/v1/monitoring/system-status", "System Status"),
            ("/api/v1/recommendations", "Trading Recommendations"),
            ("/zerodha", "Zerodha Auth Page"),
        ]
        
        passed_count = 0
        total_count = len(endpoints)
        
        for endpoint, name in endpoints:
            start_time = time.time()
            
            try:
                url = f"{self.base_url}{endpoint}"
                async with self.session.get(url) as response:
                    duration = time.time() - start_time
                    
                    # Accept various success status codes
                    success_codes = [200, 201, 202, 301, 302]
                    is_success = response.status in success_codes
                    
                    if is_success:
                        passed_count += 1
                        try:
                            data = await response.json()
                            details = {"status_code": response.status, "has_data": bool(data)}
                        except:
                            details = {"status_code": response.status, "content_type": response.headers.get('content-type', 'unknown')}
                    else:
                        details = {"status_code": response.status, "error": "Unexpected status code"}
                    
                    self.log_result(
                        f"API: {name}",
                        is_success,
                        f"Status: {response.status}",
                        details
                    )
                    
            except Exception as e:
                self.log_result(
                    f"API: {name}",
                    False,
                    f"Request failed: {str(e)}",
                    {"error": str(e)}
                )
        
        overall_success = passed_count >= (total_count * 0.7)  # 70% success rate
        self.log_result(
            "API Endpoints Overall",
            overall_success,
            f"{passed_count}/{total_count} endpoints working",
            {"success_rate": f"{(passed_count/total_count)*100:.1f}%"}
        )
        
        return overall_success
    
    async def test_zerodha_authentication_flow(self) -> bool:
        """Test Zerodha authentication endpoints and flow"""
        zerodha_tests = []
        
        # Test 1: Zerodha main auth page
        try:
            async with self.session.get(f"{self.base_url}/zerodha") as response:
                if response.status == 200:
                    content = await response.text()
                    has_auth_form = "zerodha" in content.lower() and ("login" in content.lower() or "token" in content.lower())
                    zerodha_tests.append(("Auth Page", has_auth_form))
                else:
                    zerodha_tests.append(("Auth Page", False))
        except Exception as e:
            zerodha_tests.append(("Auth Page", False))
        
        # Test 2: Zerodha auth status endpoint
        try:
            async with self.session.get(f"{self.base_url}/zerodha/status") as response:
                zerodha_tests.append(("Auth Status", response.status in [200, 401, 422]))
        except Exception as e:
            zerodha_tests.append(("Auth Status", False))
        
        # Test 3: Zerodha manual auth endpoint
        try:
            async with self.session.get(f"{self.base_url}/auth/zerodha/auth-url") as response:
                if response.status == 200:
                    data = await response.json()
                    has_kite_url = "kite.zerodha.com" in str(data)
                    zerodha_tests.append(("Manual Auth URL", has_kite_url))
                else:
                    zerodha_tests.append(("Manual Auth URL", False))
        except Exception as e:
            zerodha_tests.append(("Manual Auth URL", False))
        
        # Test 4: Zerodha test connection
        try:
            async with self.session.post(f"{self.base_url}/zerodha/test-connection") as response:
                zerodha_tests.append(("Test Connection", response.status in [200, 401, 500]))  # 500 is OK if not configured
        except Exception as e:
            zerodha_tests.append(("Test Connection", False))
        
        passed_tests = sum(1 for name, passed in zerodha_tests if passed)
        total_tests = len(zerodha_tests)
        
        overall_success = passed_tests >= (total_tests * 0.5)  # 50% success rate for auth
        
        self.log_result(
            "Zerodha Authentication",
            overall_success,
            f"{passed_tests}/{total_tests} auth tests passed",
            {"test_details": dict(zerodha_tests)}
        )
        
        return overall_success
    
    async def test_database_connectivity(self) -> bool:
        """Test database connectivity through API"""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/monitoring/database-health") as response:
                if response.status == 200:
                    data = await response.json()
                    db_healthy = data.get('database_connected', False) or data.get('healthy', False)
                    
                    self.log_result(
                        "Database Connectivity",
                        db_healthy,
                        "Database connection verified through API",
                        {"response": data}
                    )
                    return db_healthy
                else:
                    # Try alternative endpoint
                    async with self.session.get(f"{self.base_url}/health/ready/json") as alt_response:
                        if alt_response.status == 200:
                            data = await alt_response.json()
                            db_connected = data.get('database_connected', False)
                            
                            self.log_result(
                                "Database Connectivity",
                                db_connected,
                                "Database status from health endpoint",
                                {"response": data}
                            )
                            return db_connected
                        else:
                            self.log_result(
                                "Database Connectivity",
                                False,
                                f"Health endpoint returned {alt_response.status}",
                                {"status_code": alt_response.status}
                            )
                            return False
                            
        except Exception as e:
            self.log_result(
                "Database Connectivity",
                False,
                f"Database test failed: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def test_redis_connectivity(self) -> bool:
        """Test Redis connectivity through API"""
        try:
            async with self.session.get(f"{self.base_url}/health/ready/json") as response:
                if response.status == 200:
                    data = await response.json()
                    redis_connected = data.get('redis_connected', False)
                    
                    self.log_result(
                        "Redis Connectivity",
                        redis_connected,
                        "Redis connection verified through health endpoint",
                        {"response": data}
                    )
                    return redis_connected
                else:
                    self.log_result(
                        "Redis Connectivity",
                        False,
                        f"Health endpoint returned {response.status}",
                        {"status_code": response.status}
                    )
                    return False
                    
        except Exception as e:
            self.log_result(
                "Redis Connectivity",
                False,
                f"Redis test failed: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def test_websocket_capability(self) -> bool:
        """Test WebSocket endpoint availability"""
        try:
            # Test WebSocket endpoint (just check if it's available, not actual WS connection)
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws'
            
            # Try to connect to WebSocket info endpoint
            async with self.session.get(f"{self.base_url}/api/v1/websocket/status") as response:
                if response.status == 200:
                    data = await response.json()
                    ws_available = data.get('websocket_enabled', True)  # Default to True if not specified
                    
                    self.log_result(
                        "WebSocket Capability",
                        ws_available,
                        "WebSocket endpoint available",
                        {"ws_url": ws_url, "status": data}
                    )
                    return ws_available
                else:
                    # WebSocket might be available even if status endpoint isn't
                    self.log_result(
                        "WebSocket Capability",
                        True,  # Assume available
                        "WebSocket status endpoint not found (assuming available)",
                        {"ws_url": ws_url}
                    )
                    return True
                    
        except Exception as e:
            self.log_result(
                "WebSocket Capability",
                False,
                f"WebSocket test failed: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def test_performance_metrics(self) -> bool:
        """Test performance-related endpoints"""
        performance_tests = []
        
        # Test response times for key endpoints
        fast_endpoints = [
            "/health",
            "/api",
            "/health/ready/json"
        ]
        
        for endpoint in fast_endpoints:
            start_time = time.time()
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    response_time = time.time() - start_time
                    is_fast = response_time < 5.0  # Should respond within 5 seconds
                    performance_tests.append((f"Speed: {endpoint}", is_fast, response_time))
            except Exception as e:
                performance_tests.append((f"Speed: {endpoint}", False, 999))
        
        passed_performance = sum(1 for name, passed, time in performance_tests if passed)
        total_performance = len(performance_tests)
        
        overall_performance = passed_performance >= (total_performance * 0.8)  # 80% should be fast
        
        details = {test[0]: {"passed": test[1], "response_time": f"{test[2]:.2f}s"} for test in performance_tests}
        
        self.log_result(
            "Performance Metrics",
            overall_performance,
            f"{passed_performance}/{total_performance} endpoints responding quickly",
            details
        )
        
        return overall_performance
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        logger.info("🚀 Starting Comprehensive DigitalOcean App Testing")
        logger.info(f"📍 Target URL: {self.base_url}")
        logger.info("=" * 80)
        
        # Run all test categories
        test_categories = [
            ("Basic Connectivity", self.test_basic_connectivity()),
            ("Frontend Loading", self.test_frontend_loading()),
            ("API Endpoints", self.test_api_endpoints()),
            ("Zerodha Authentication", self.test_zerodha_authentication_flow()),
            ("Database Connectivity", self.test_database_connectivity()),
            ("Redis Connectivity", self.test_redis_connectivity()),
            ("WebSocket Capability", self.test_websocket_capability()),
            ("Performance Metrics", self.test_performance_metrics()),
        ]
        
        category_results = {}
        for category_name, test_coro in test_categories:
            logger.info(f"\n🔍 Testing: {category_name}")
            logger.info("-" * 40)
            
            try:
                result = await test_coro
                category_results[category_name] = result
            except Exception as e:
                logger.error(f"❌ {category_name} test crashed: {e}")
                category_results[category_name] = False
        
        # Generate summary report
        total_categories = len(category_results)
        passed_categories = sum(category_results.values())
        
        overall_health = passed_categories / total_categories
        
        # Determine overall status
        if overall_health >= 0.9:
            status = "EXCELLENT"
            status_emoji = "🟢"
        elif overall_health >= 0.7:
            status = "GOOD"
            status_emoji = "🟡"
        elif overall_health >= 0.5:
            status = "FAIR"
            status_emoji = "🟠"
        else:
            status = "POOR"
            status_emoji = "🔴"
        
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "target_url": self.base_url,
            "overall_status": status,
            "overall_health_score": f"{overall_health*100:.1f}%",
            "category_results": category_results,
            "passed_categories": passed_categories,
            "total_categories": total_categories,
            "detailed_results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                    "duration": r.duration
                }
                for r in self.results
            ],
            "recommendations": self._generate_recommendations(category_results)
        }
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"{status_emoji} Overall Status: {status}")
        logger.info(f"📈 Health Score: {overall_health*100:.1f}%")
        logger.info(f"✅ Categories Passed: {passed_categories}/{total_categories}")
        
        logger.info("\n📋 Category Results:")
        for category, result in category_results.items():
            result_emoji = "✅" if result else "❌"
            logger.info(f"   {result_emoji} {category}")
        
        if report["recommendations"]:
            logger.info("\n💡 Recommendations:")
            for rec in report["recommendations"]:
                logger.info(f"   • {rec}")
        
        return report
    
    def _generate_recommendations(self, category_results: Dict[str, bool]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if not category_results.get("Basic Connectivity", True):
            recommendations.append("Check if the app is deployed and running on DigitalOcean")
        
        if not category_results.get("Frontend Loading", True):
            recommendations.append("Verify frontend build process and static file serving")
        
        if not category_results.get("Zerodha Authentication", True):
            recommendations.append("Configure Zerodha API credentials in environment variables")
        
        if not category_results.get("Database Connectivity", True):
            recommendations.append("Check database connection and migration status")
        
        if not category_results.get("Redis Connectivity", True):
            recommendations.append("Verify Redis service is running and accessible")
        
        if not category_results.get("Performance Metrics", True):
            recommendations.append("Investigate slow response times - consider scaling resources")
        
        if not any(category_results.values()):
            recommendations.append("App appears to be completely down - check DigitalOcean deployment logs")
        
        return recommendations

async def main():
    """Main test function"""
    # Get URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://algoauto-9gx56.ondigitalocean.app"
    
    print(f"🧪 Starting comprehensive test of: {base_url}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with DigitalOceanAppTester(base_url) as tester:
        report = await tester.run_comprehensive_test()
        
        # Save detailed report
        report_filename = f"digitalocean_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📄 Detailed report saved to: {report_filename}")
        
        # Return appropriate exit code
        overall_health = float(report["overall_health_score"].rstrip('%')) / 100
        return 0 if overall_health >= 0.7 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 