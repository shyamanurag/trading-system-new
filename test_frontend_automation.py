#!/usr/bin/env python3
"""
🌐 FRONTEND AUTOMATION TEST (Simplified)
========================================

This script tests frontend functionality without requiring browser drivers.
Uses requests to test frontend endpoints and validate responses.
"""

import sys
import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FrontendTester:
    """Frontend functionality tester"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AlgoAuto-Frontend-Test/1.0',
            'Accept': 'text/html,application/json,*/*'
        })
        self.results = []
    
    def log_result(self, test_name: str, passed: bool, message: str, details: Dict = None):
        """Log test result"""
        self.results.append({
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "details": details or {}
        })
        
        status = "✅" if passed else "❌"
        logger.info(f"{status} {test_name}: {message}")
    
    def test_frontend_pages(self) -> bool:
        """Test frontend page accessibility"""
        pages = [
            ("/", "Homepage"),
            ("/zerodha", "Zerodha Auth Page"),
            ("/docs", "API Documentation"),
            ("/health", "Health Check")
        ]
        
        passed_pages = 0
        for path, name in pages:
            try:
                response = self.session.get(f"{self.base_url}{path}", timeout=10)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Check for frontend indicators
                    frontend_checks = {
                        "html_structure": "<!DOCTYPE html>" in content,
                        "has_head": "<head>" in content,
                        "has_body": "<body>" in content,
                        "has_title": "<title>" in content,
                        "reasonable_size": len(content) > 500
                    }
                    
                    check_score = sum(frontend_checks.values())
                    page_success = check_score >= 3
                    
                    if page_success:
                        passed_pages += 1
                    
                    self.log_result(
                        f"Frontend Page: {name}",
                        page_success,
                        f"Page checks: {check_score}/5",
                        {"url": path, "checks": frontend_checks}
                    )
                else:
                    self.log_result(
                        f"Frontend Page: {name}",
                        False,
                        f"HTTP {response.status_code}",
                        {"url": path}
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Frontend Page: {name}",
                    False,
                    f"Request failed: {str(e)}",
                    {"url": path}
                )
        
        overall_success = passed_pages >= len(pages) * 0.75
        self.log_result(
            "Frontend Pages Overall",
            overall_success,
            f"{passed_pages}/{len(pages)} pages working",
            {"success_rate": f"{(passed_pages/len(pages))*100:.1f}%"}
        )
        
        return overall_success
    
    def test_zerodha_auth_interface(self) -> bool:
        """Test Zerodha authentication interface"""
        auth_endpoints = [
            ("/zerodha", "Main Auth Page"),
            ("/zerodha/status", "Auth Status"),
            ("/auth/zerodha/auth-url", "Manual Auth URL"),
            ("/zerodha-multi", "Multi-user Auth")
        ]
        
        auth_results = []
        for endpoint, name in auth_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code in [200, 401]:  # 401 is OK for auth endpoints
                    content = response.text.lower()
                    
                    # Check for auth-related content
                    auth_indicators = {
                        "zerodha_mentioned": "zerodha" in content,
                        "auth_content": any(word in content for word in ["login", "authenticate", "token", "api"]),
                        "form_elements": any(word in content for word in ["form", "input", "button"]),
                        "kite_reference": "kite" in content or "zerodha.com" in content
                    }
                    
                    auth_score = sum(auth_indicators.values())
                    auth_success = auth_score >= 2
                    auth_results.append(auth_success)
                    
                    self.log_result(
                        f"Zerodha Auth: {name}",
                        auth_success,
                        f"Auth indicators: {auth_score}/4",
                        {"endpoint": endpoint, "indicators": auth_indicators}
                    )
                else:
                    auth_results.append(False)
                    self.log_result(
                        f"Zerodha Auth: {name}",
                        False,
                        f"HTTP {response.status_code}",
                        {"endpoint": endpoint}
                    )
                    
            except Exception as e:
                auth_results.append(False)
                self.log_result(
                    f"Zerodha Auth: {name}",
                    False,
                    f"Request failed: {str(e)}",
                    {"endpoint": endpoint}
                )
        
        overall_auth_success = sum(auth_results) >= len(auth_results) * 0.5
        self.log_result(
            "Zerodha Auth Interface",
            overall_auth_success,
            f"{sum(auth_results)}/{len(auth_results)} auth endpoints working"
        )
        
        return overall_auth_success
    
    def test_api_frontend_integration(self) -> bool:
        """Test API endpoints that frontend likely uses"""
        api_endpoints = [
            ("/api", "API Root"),
            ("/api/auth/me", "Auth Status"),
            ("/api/v1/market/indices", "Market Data"),
            ("/api/v1/monitoring/system-status", "System Status"),
            ("/health/ready/json", "Health JSON"),
            ("/api/v1/recommendations", "Trading Recommendations")
        ]
        
        api_results = []
        for endpoint, name in api_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                # Accept various status codes that frontend can handle
                acceptable_codes = [200, 201, 401, 422, 404]  # 404 is OK if endpoint doesn't exist
                code_ok = response.status_code in acceptable_codes
                
                content_type = response.headers.get('content-type', '').lower()
                
                # Check if response is JSON (preferred for API)
                is_json = 'application/json' in content_type
                
                # Try to parse JSON if it claims to be JSON
                json_valid = True
                if is_json:
                    try:
                        json.loads(response.text)
                    except:
                        json_valid = False
                
                api_success = code_ok and (is_json and json_valid or response.status_code == 404)
                api_results.append(api_success)
                
                self.log_result(
                    f"API Integration: {name}",
                    api_success,
                    f"Status: {response.status_code}, JSON: {is_json and json_valid}",
                    {
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "content_type": content_type,
                        "json_valid": json_valid
                    }
                )
                
            except Exception as e:
                api_results.append(False)
                self.log_result(
                    f"API Integration: {name}",
                    False,
                    f"Request failed: {str(e)}",
                    {"endpoint": endpoint}
                )
        
        overall_api_success = sum(api_results) >= len(api_results) * 0.7
        self.log_result(
            "API Frontend Integration",
            overall_api_success,
            f"{sum(api_results)}/{len(api_results)} API endpoints accessible"
        )
        
        return overall_api_success
    
    def test_static_assets(self) -> bool:
        """Test static asset loading"""
        # Test common static asset paths
        static_paths = [
            "/favicon.ico",
            "/manifest.json",
            "/robots.txt"
        ]
        
        static_results = []
        for path in static_paths:
            try:
                response = self.session.get(f"{self.base_url}{path}", timeout=5)
                # 200 (found) or 404 (not found but server responsive) are both acceptable
                asset_success = response.status_code in [200, 404]
                static_results.append(asset_success)
                
                self.log_result(
                    f"Static Asset: {path}",
                    asset_success,
                    f"Status: {response.status_code}",
                    {"path": path, "status": response.status_code}
                )
                
            except Exception as e:
                static_results.append(False)
                self.log_result(
                    f"Static Asset: {path}",
                    False,
                    f"Request failed: {str(e)}",
                    {"path": path}
                )
        
        # At least one static asset test should pass (server is responsive)
        overall_static_success = sum(static_results) >= 1
        self.log_result(
            "Static Assets",
            overall_static_success,
            f"{sum(static_results)}/{len(static_results)} static asset tests passed"
        )
        
        return overall_static_success
    
    def test_cors_and_headers(self) -> bool:
        """Test CORS and security headers"""
        try:
            # Test CORS with an OPTIONS request
            response = self.session.options(f"{self.base_url}/api", timeout=10)
            
            headers = response.headers
            
            cors_checks = {
                "cors_origin": headers.get('Access-Control-Allow-Origin') is not None,
                "cors_methods": headers.get('Access-Control-Allow-Methods') is not None,
                "cors_headers": headers.get('Access-Control-Allow-Headers') is not None,
                "content_type": headers.get('Content-Type') is not None,
                "server_responsive": response.status_code < 500
            }
            
            cors_score = sum(cors_checks.values())
            cors_success = cors_score >= 3
            
            self.log_result(
                "CORS and Headers",
                cors_success,
                f"Header checks: {cors_score}/5",
                {"checks": cors_checks, "headers": dict(headers)}
            )
            
            return cors_success
            
        except Exception as e:
            self.log_result(
                "CORS and Headers",
                False,
                f"CORS test failed: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all frontend tests"""
        logger.info("🌐 Starting Frontend Automation Tests")
        logger.info(f"📍 Target URL: {self.base_url}")
        logger.info("=" * 60)
        
        test_categories = [
            ("Frontend Pages", self.test_frontend_pages),
            ("Zerodha Auth Interface", self.test_zerodha_auth_interface),
            ("API Frontend Integration", self.test_api_frontend_integration),
            ("Static Assets", self.test_static_assets),
            ("CORS and Headers", self.test_cors_and_headers)
        ]
        
        category_results = {}
        for test_name, test_method in test_categories:
            logger.info(f"\n🔍 Testing: {test_name}")
            try:
                result = test_method()
                category_results[test_name] = result
            except Exception as e:
                logger.error(f"❌ {test_name} crashed: {e}")
                category_results[test_name] = False
        
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
            "test_type": "Frontend Automation (Simplified)",
            "overall_status": status,
            "score": f"{score:.1f}%",
            "passed_categories": passed,
            "total_categories": total,
            "category_results": category_results,
            "detailed_results": self.results
        }
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 FRONTEND TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"🎯 Overall Status: {status}")
        logger.info(f"📈 Score: {score:.1f}%")
        logger.info(f"✅ Passed: {passed}/{total} categories")
        
        for category, result in category_results.items():
            emoji = "✅" if result else "❌"
            logger.info(f"   {emoji} {category}")
        
        return report

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://algoauto-9gx56.ondigitalocean.app"
    
    print(f"🌐 Testing frontend: {base_url}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = FrontendTester(base_url)
    report = tester.run_all_tests()
    
    # Save report
    filename = f"frontend_automation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\n📄 Frontend test report saved: {filename}")
    
    # Exit code based on score
    score = float(report["score"].rstrip('%'))
    return 0 if score >= 70 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test runner failed: {e}")
        sys.exit(1) 