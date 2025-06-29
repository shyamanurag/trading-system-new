#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE DIGITALOCEAN DEPLOYMENT TEST SUITE
===================================================

This script tests the deployed DigitalOcean application comprehensively,
including frontend, Zerodha authentication, and system health.

Usage: python test_digitalocean_deployment.py [URL]
"""

import sys
import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    details: Optional[Dict] = None

class DigitalOceanTester:
    """Comprehensive tester for DigitalOcean deployed app"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, name: str, passed: bool, message: str, details: Dict = None):
        result = TestResult(name, passed, message, details)
        self.results.append(result)
        status = "✅" if passed else "❌"
        logger.info(f"{status} {name}: {message}")
    
    async def test_basic_connectivity(self) -> bool:
        """Test basic connectivity"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("Basic Connectivity", True, "App is reachable", {"response": data})
                    return True
                else:
                    self.log_result("Basic Connectivity", False, f"Health endpoint returned {response.status}")
                    return False
        except Exception as e:
            self.log_result("Basic Connectivity", False, f"Connection failed: {str(e)}")
            return False
    
    async def test_frontend_loading(self) -> bool:
        """Test frontend loading"""
        try:
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    checks = {
                        "HTML": "<!DOCTYPE html>" in html_content,
                        "React/Vite": any(x in html_content.lower() for x in ["react", "vite"]),
                        "Trading App": any(x in html_content.lower() for x in ["trading", "dashboard"]),
                        "Styles": any(x in html_content for x in ["<style", ".css"]),
                        "Scripts": any(x in html_content for x in ["<script", ".js"])
                    }
                    
                    passed_checks = sum(checks.values())
                    success = passed_checks >= 3
                    
                    self.log_result("Frontend Loading", success, f"Frontend checks: {passed_checks}/5", {"checks": checks})
                    return success
                else:
                    self.log_result("Frontend Loading", False, f"Frontend returned {response.status}")
                    return False
        except Exception as e:
            self.log_result("Frontend Loading", False, f"Frontend loading failed: {str(e)}")
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Test API endpoints"""
        endpoints = [
            ("/health", "Health Check"),
            ("/health/ready/json", "Health Ready"),
            ("/api", "API Root"),
            ("/api/auth/me", "Auth Status"),
            ("/api/v1/market/indices", "Market Indices"),
            ("/api/v1/monitoring/system-status", "System Status"),
            ("/zerodha", "Zerodha Auth Page"),
        ]
        
        passed_count = 0
        for endpoint, name in endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    success = response.status in [200, 201, 301, 302, 401]  # Various acceptable codes
                    if success:
                        passed_count += 1
                    self.log_result(f"API: {name}", success, f"Status: {response.status}")
            except Exception as e:
                self.log_result(f"API: {name}", False, f"Failed: {str(e)}")
        
        overall_success = passed_count >= len(endpoints) * 0.7  # 70% success rate
        self.log_result("API Endpoints", overall_success, f"{passed_count}/{len(endpoints)} working")
        return overall_success
    
    async def test_zerodha_auth(self) -> bool:
        """Test Zerodha authentication"""
        auth_tests = []
        
        # Test Zerodha auth page
        try:
            async with self.session.get(f"{self.base_url}/zerodha") as response:
                success = response.status == 200
                if success:
                    content = await response.text()
                    has_auth = "zerodha" in content.lower() and "login" in content.lower()
                    auth_tests.append(("Auth Page", has_auth))
                else:
                    auth_tests.append(("Auth Page", False))
        except:
            auth_tests.append(("Auth Page", False))
        
        # Test auth status
        try:
            async with self.session.get(f"{self.base_url}/zerodha/status") as response:
                auth_tests.append(("Auth Status", response.status in [200, 401]))
        except:
            auth_tests.append(("Auth Status", False))
        
        # Test manual auth
        try:
            async with self.session.get(f"{self.base_url}/auth/zerodha/auth-url") as response:
                if response.status == 200:
                    data = await response.json()
                    has_kite = "kite.zerodha.com" in str(data)
                    auth_tests.append(("Manual Auth", has_kite))
                else:
                    auth_tests.append(("Manual Auth", False))
        except:
            auth_tests.append(("Manual Auth", False))
        
        passed = sum(1 for _, success in auth_tests if success)
        overall_success = passed >= len(auth_tests) * 0.5
        
        self.log_result("Zerodha Auth", overall_success, f"{passed}/{len(auth_tests)} auth tests passed")
        return overall_success
    
    async def test_system_health(self) -> bool:
        """Test system health"""
        try:
            async with self.session.get(f"{self.base_url}/health/ready/json") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    health_checks = {
                        "database": data.get('database_connected', False),
                        "redis": data.get('redis_connected', False),
                        "ready": data.get('ready', False),
                        "trading": data.get('trading_enabled', False)
                    }
                    
                    healthy_count = sum(health_checks.values())
                    overall_healthy = healthy_count >= 2  # At least 2 components should be healthy
                    
                    self.log_result("System Health", overall_healthy, f"Health: {healthy_count}/4 systems OK", health_checks)
                    return overall_healthy
                else:
                    self.log_result("System Health", False, f"Health endpoint returned {response.status}")
                    return False
        except Exception as e:
            self.log_result("System Health", False, f"Health check failed: {str(e)}")
            return False
    
    async def test_performance(self) -> bool:
        """Test performance"""
        fast_endpoints = ["/health", "/api"]
        performance_results = []
        
        for endpoint in fast_endpoints:
            start_time = time.time()
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    response_time = time.time() - start_time
                    is_fast = response_time < 3.0
                    performance_results.append(is_fast)
                    self.log_result(f"Performance: {endpoint}", is_fast, f"Response: {response_time:.2f}s")
            except:
                performance_results.append(False)
        
        overall_performance = sum(performance_results) >= len(performance_results) * 0.8
        self.log_result("Performance", overall_performance, "Response times acceptable")
        return overall_performance
    
    async def run_all_tests(self) -> Dict:
        """Run all tests"""
        logger.info(f"🚀 Testing DigitalOcean app: {self.base_url}")
        logger.info("=" * 60)
        
        test_categories = [
            ("Basic Connectivity", self.test_basic_connectivity()),
            ("Frontend Loading", self.test_frontend_loading()),
            ("API Endpoints", self.test_api_endpoints()),
            ("Zerodha Authentication", self.test_zerodha_auth()),
            ("System Health", self.test_system_health()),
            ("Performance", self.test_performance()),
        ]
        
        category_results = {}
        for name, test_coro in test_categories:
            logger.info(f"\n🔍 Testing: {name}")
            try:
                result = await test_coro
                category_results[name] = result
            except Exception as e:
                logger.error(f"❌ {name} crashed: {e}")
                category_results[name] = False
        
        # Calculate overall score
        passed = sum(category_results.values())
        total = len(category_results)
        score = (passed / total) * 100
        
        # Determine status
        if score >= 90:
            status = "EXCELLENT 🟢"
        elif score >= 75:
            status = "GOOD 🟡"
        elif score >= 50:
            status = "FAIR 🟠"
        else:
            status = "POOR 🔴"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "url": self.base_url,
            "overall_status": status,
            "score": f"{score:.1f}%",
            "passed_categories": passed,
            "total_categories": total,
            "category_results": category_results,
            "detailed_results": [
                {"name": r.name, "passed": r.passed, "message": r.message, "details": r.details}
                for r in self.results
            ]
        }
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"🎯 Overall Status: {status}")
        logger.info(f"📈 Score: {score:.1f}%")
        logger.info(f"✅ Passed: {passed}/{total} categories")
        
        for category, result in category_results.items():
            emoji = "✅" if result else "❌"
            logger.info(f"   {emoji} {category}")
        
        return report

async def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://algoauto-9gx56.ondigitalocean.app"
    
    print(f"🧪 Testing deployed app: {base_url}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with DigitalOceanTester(base_url) as tester:
        report = await tester.run_all_tests()
        
        # Save report
        filename = f"digitalocean_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📄 Report saved: {filename}")
        
        # Exit code based on score
        score = float(report["score"].rstrip('%'))
        return 0 if score >= 70 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 