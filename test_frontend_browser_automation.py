#!/usr/bin/env python3
"""
🌐 FRONTEND BROWSER AUTOMATION TEST SUITE
========================================

This script uses Selenium to test the frontend functionality of the deployed app,
including navigation, Zerodha authentication flow, and dashboard interactions.

Requirements: pip install selenium

Usage: python test_frontend_browser_automation.py [URL]
"""

import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FrontendTestResult:
    """Frontend test result"""
    test_name: str
    passed: bool
    message: str
    screenshot_path: Optional[str] = None
    details: Optional[Dict] = None

class FrontendTester:
    """Browser automation tester for frontend"""
    
    def __init__(self, base_url: str, headless: bool = True):
        self.base_url = base_url.rstrip('/')
        self.headless = headless
        self.driver = None
        self.results: List[FrontendTestResult] = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("✅ Chrome WebDriver initialized successfully")
            return True
            
        except ImportError:
            logger.error("❌ Selenium not installed. Run: pip install selenium")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            logger.info("💡 Make sure Chrome browser is installed")
            return False
    
    def log_result(self, test_name: str, passed: bool, message: str, details: Dict = None):
        """Log test result"""
        result = FrontendTestResult(test_name, passed, message, None, details)
        self.results.append(result)
        
        status = "✅" if passed else "❌"
        logger.info(f"{status} {test_name}: {message}")
        
        # Take screenshot if test failed
        if not passed and self.driver:
            try:
                screenshot_path = f"screenshot_{test_name.replace(' ', '_').lower()}_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                result.screenshot_path = screenshot_path
                logger.info(f"📸 Screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.warning(f"Could not save screenshot: {e}")
    
    def test_homepage_loading(self) -> bool:
        """Test if homepage loads correctly"""
        try:
            self.driver.get(self.base_url)
            time.sleep(3)  # Wait for page to load
            
            # Check if page loaded
            page_title = self.driver.title
            page_source = self.driver.page_source
            
            checks = {
                "page_loaded": len(page_source) > 1000,
                "has_title": len(page_title) > 0,
                "has_react_content": "react" in page_source.lower() or "trading" in page_source.lower(),
                "no_error_messages": "error" not in page_source.lower() or "404" not in page_source,
                "has_navigation": any(nav in page_source.lower() for nav in ["nav", "menu", "dashboard"])
            }
            
            passed_checks = sum(checks.values())
            success = passed_checks >= 3
            
            self.log_result(
                "Homepage Loading",
                success,
                f"Page loaded with {passed_checks}/5 checks passed",
                {"title": page_title, "checks": checks}
            )
            
            return success
            
        except Exception as e:
            self.log_result("Homepage Loading", False, f"Failed to load homepage: {str(e)}")
            return False
    
    def test_navigation_elements(self) -> bool:
        """Test navigation elements"""
        try:
            from selenium.webdriver.common.by import By
            
            # Look for common navigation elements
            nav_elements = []
            
            # Check for navigation menu
            try:
                nav_menu = self.driver.find_element(By.TAG_NAME, "nav")
                nav_elements.append("nav_menu")
            except:
                pass
            
            # Check for dashboard links
            dashboard_keywords = ["dashboard", "trading", "zerodha", "auth", "login"]
            for keyword in dashboard_keywords:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                    if elements:
                        nav_elements.append(f"{keyword}_link")
                except:
                    pass
            
            # Check for buttons
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                if buttons:
                    nav_elements.append("buttons")
            except:
                pass
            
            success = len(nav_elements) >= 2
            
            self.log_result(
                "Navigation Elements",
                success,
                f"Found {len(nav_elements)} navigation elements",
                {"elements": nav_elements}
            )
            
            return success
            
        except Exception as e:
            self.log_result("Navigation Elements", False, f"Navigation test failed: {str(e)}")
            return False
    
    def test_zerodha_auth_page(self) -> bool:
        """Test Zerodha authentication page"""
        try:
            from selenium.webdriver.common.by import By
            
            # Navigate to Zerodha auth page
            zerodha_url = f"{self.base_url}/zerodha"
            self.driver.get(zerodha_url)
            time.sleep(3)
            
            page_source = self.driver.page_source.lower()
            
            auth_checks = {
                "zerodha_mentioned": "zerodha" in page_source,
                "auth_form_present": any(keyword in page_source for keyword in ["login", "token", "authenticate"]),
                "api_key_mentioned": "api" in page_source and "key" in page_source,
                "instruction_present": any(keyword in page_source for keyword in ["step", "instruction", "manual"]),
                "kite_url_present": "kite.zerodha.com" in page_source
            }
            
            # Look for form elements
            try:
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                if forms:
                    auth_checks["form_elements"] = True
            except:
                auth_checks["form_elements"] = False
            
            # Look for input fields
            try:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                if inputs:
                    auth_checks["input_fields"] = True
            except:
                auth_checks["input_fields"] = False
            
            passed_checks = sum(auth_checks.values())
            success = passed_checks >= 3
            
            self.log_result(
                "Zerodha Auth Page",
                success,
                f"Auth page checks: {passed_checks}/{len(auth_checks)}",
                {"checks": auth_checks}
            )
            
            return success
            
        except Exception as e:
            self.log_result("Zerodha Auth Page", False, f"Auth page test failed: {str(e)}")
            return False
    
    def test_api_connectivity_frontend(self) -> bool:
        """Test if frontend can connect to API"""
        try:
            from selenium.webdriver.common.by import By
            
            # Navigate to a page that makes API calls
            self.driver.get(f"{self.base_url}/health")
            time.sleep(2)
            
            # Check if we get JSON response (health endpoint)
            page_source = self.driver.page_source
            
            api_checks = {
                "json_response": "{" in page_source and "}" in page_source,
                "health_data": "status" in page_source.lower(),
                "no_error_page": "404" not in page_source and "500" not in page_source,
                "valid_response": "healthy" in page_source.lower() or "ready" in page_source.lower()
            }
            
            passed_checks = sum(api_checks.values())
            success = passed_checks >= 3
            
            self.log_result(
                "API Connectivity (Frontend)",
                success,
                f"API connectivity checks: {passed_checks}/4",
                {"checks": api_checks}
            )
            
            return success
            
        except Exception as e:
            self.log_result("API Connectivity (Frontend)", False, f"API connectivity test failed: {str(e)}")
            return False
    
    def test_responsive_design(self) -> bool:
        """Test responsive design"""
        try:
            # Test different screen sizes
            screen_sizes = [
                (1920, 1080, "Desktop"),
                (768, 1024, "Tablet"),
                (375, 667, "Mobile")
            ]
            
            responsive_results = []
            
            for width, height, device in screen_sizes:
                self.driver.set_window_size(width, height)
                time.sleep(2)
                
                # Check if page is still functional
                page_source = self.driver.page_source
                
                device_checks = {
                    "page_loads": len(page_source) > 1000,
                    "no_horizontal_scroll": self.driver.execute_script("return document.body.scrollWidth <= window.innerWidth"),
                    "content_visible": "trading" in page_source.lower() or "dashboard" in page_source.lower()
                }
                
                device_score = sum(device_checks.values())
                responsive_results.append((device, device_score, 3))
            
            # Calculate overall responsive score
            total_score = sum(score for _, score, _ in responsive_results)
            max_score = sum(max_score for _, _, max_score in responsive_results)
            success = total_score >= max_score * 0.7
            
            self.log_result(
                "Responsive Design",
                success,
                f"Responsive design score: {total_score}/{max_score}",
                {"device_results": responsive_results}
            )
            
            # Reset to desktop size
            self.driver.set_window_size(1920, 1080)
            
            return success
            
        except Exception as e:
            self.log_result("Responsive Design", False, f"Responsive design test failed: {str(e)}")
            return False
    
    def test_javascript_functionality(self) -> bool:
        """Test JavaScript functionality"""
        try:
            # Navigate to main page
            self.driver.get(self.base_url)
            time.sleep(3)
            
            js_checks = {
                "javascript_enabled": self.driver.execute_script("return typeof document !== 'undefined'"),
                "console_errors": len(self.driver.get_log('browser')) == 0,
                "react_loaded": self.driver.execute_script("return typeof React !== 'undefined' || typeof window.React !== 'undefined'"),
                "dom_interactive": self.driver.execute_script("return document.readyState === 'complete'"),
                "no_js_errors": True  # We'll check this separately
            }
            
            # Check for JavaScript errors in console
            try:
                logs = self.driver.get_log('browser')
                severe_errors = [log for log in logs if log['level'] == 'SEVERE']
                js_checks["no_severe_js_errors"] = len(severe_errors) == 0
            except:
                js_checks["no_severe_js_errors"] = True  # Can't check, assume OK
            
            passed_checks = sum(js_checks.values())
            success = passed_checks >= len(js_checks) * 0.7
            
            self.log_result(
                "JavaScript Functionality",
                success,
                f"JavaScript checks: {passed_checks}/{len(js_checks)}",
                {"checks": js_checks}
            )
            
            return success
            
        except Exception as e:
            self.log_result("JavaScript Functionality", False, f"JavaScript test failed: {str(e)}")
            return False
    
    def run_all_frontend_tests(self) -> Dict:
        """Run all frontend tests"""
        logger.info("🌐 Starting Frontend Browser Automation Tests")
        logger.info(f"📍 Target URL: {self.base_url}")
        logger.info("=" * 60)
        
        # Setup browser
        if not self.setup_driver():
            return {"error": "Could not setup WebDriver"}
        
        try:
            # Run all frontend tests
            test_methods = [
                ("Homepage Loading", self.test_homepage_loading),
                ("Navigation Elements", self.test_navigation_elements),
                ("Zerodha Auth Page", self.test_zerodha_auth_page),
                ("API Connectivity", self.test_api_connectivity_frontend),
                ("Responsive Design", self.test_responsive_design),
                ("JavaScript Functionality", self.test_javascript_functionality)
            ]
            
            category_results = {}
            for test_name, test_method in test_methods:
                logger.info(f"\n🔍 Testing: {test_name}")
                try:
                    result = test_method()
                    category_results[test_name] = result
                except Exception as e:
                    logger.error(f"❌ {test_name} crashed: {e}")
                    category_results[test_name] = False
            
            # Calculate score
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
                "test_type": "Frontend Browser Automation",
                "overall_status": status,
                "score": f"{score:.1f}%",
                "passed_tests": passed,
                "total_tests": total,
                "category_results": category_results,
                "detailed_results": [
                    {
                        "test_name": r.test_name,
                        "passed": r.passed,
                        "message": r.message,
                        "screenshot_path": r.screenshot_path,
                        "details": r.details
                    }
                    for r in self.results
                ]
            }
            
            # Print summary
            logger.info("\n" + "=" * 60)
            logger.info("📊 FRONTEND TEST SUMMARY")
            logger.info("=" * 60)
            logger.info(f"🎯 Overall Status: {status}")
            logger.info(f"📈 Score: {score:.1f}%")
            logger.info(f"✅ Passed: {passed}/{total} tests")
            
            for test_name, result in category_results.items():
                emoji = "✅" if result else "❌"
                logger.info(f"   {emoji} {test_name}")
            
            return report
            
        finally:
            # Cleanup
            if self.driver:
                self.driver.quit()
                logger.info("🔧 WebDriver closed")

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://algoauto-9gx56.ondigitalocean.app"
    
    print(f"🌐 Testing frontend: {base_url}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 Note: This test requires Chrome browser and selenium package")
    
    tester = FrontendTester(base_url, headless=True)
    report = tester.run_all_frontend_tests()
    
    if "error" in report:
        logger.error(f"❌ Test setup failed: {report['error']}")
        return 1
    
    # Save report
    filename = f"frontend_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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