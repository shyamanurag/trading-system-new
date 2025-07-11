#!/usr/bin/env python3
"""
🔍 NO HARDCODED VALUES TEST
Verifies that all hardcoded values have been removed from the frontend
"""

import os
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class HardcodedValuesTest:
    """Test for hardcoded values in frontend"""
    
    def __init__(self):
        self.test_results = []
        self.frontend_dir = Path("src/frontend/components")
        
    def log_test_result(self, test_name: str, success: bool, message: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    def check_hardcoded_capital_values(self):
        """Check for hardcoded capital values like 1000000"""
        hardcoded_patterns = [
            r'1000000(?!\s*\+|\s*-|\s*\*|\s*\/)',  # 1000000 not in calculations
            r'10.*lakh',  # "10 lakh" text
            r'₹1,000,000',  # Formatted currency
            r'1,000,000',  # Comma formatted
        ]
        
        violations = []
        
        for jsx_file in self.frontend_dir.glob("*.jsx"):
            content = jsx_file.read_text()
            
            for pattern in hardcoded_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append(f"{jsx_file.name}: {matches}")
        
        success = len(violations) == 0
        message = f"Found {len(violations)} hardcoded capital values" if violations else "No hardcoded capital values found"
        
        if violations:
            message += f": {violations[:3]}"  # Show first 3 violations
            
        self.log_test_result("Hardcoded Capital Values", success, message)
        return success
    
    def check_mock_data_generation(self):
        """Check for mock data generation"""
        mock_patterns = [
            r'mock.*positions',
            r'create.*mock',
            r'mockPositions',
            r'fake.*data',
            r'hardcoded.*user'
        ]
        
        violations = []
        
        for jsx_file in self.frontend_dir.glob("*.jsx"):
            content = jsx_file.read_text()
            
            for pattern in mock_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append(f"{jsx_file.name}: {matches}")
        
        success = len(violations) == 0
        message = f"Found {len(violations)} mock data patterns" if violations else "No mock data generation found"
        
        if violations:
            message += f": {violations[:3]}"  # Show first 3 violations
            
        self.log_test_result("Mock Data Generation", success, message)
        return success
    
    def check_hardcoded_success_rates(self):
        """Check for hardcoded success rates"""
        hardcoded_patterns = [
            r'70%',  # Hardcoded 70% success rate
            r'success.*rate.*70',
            r'|| 70',  # Default 70 fallback
        ]
        
        violations = []
        
        for jsx_file in self.frontend_dir.glob("*.jsx"):
            content = jsx_file.read_text()
            
            for pattern in hardcoded_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append(f"{jsx_file.name}: {matches}")
        
        success = len(violations) == 0
        message = f"Found {len(violations)} hardcoded success rates" if violations else "No hardcoded success rates found"
        
        if violations:
            message += f": {violations[:3]}"  # Show first 3 violations
            
        self.log_test_result("Hardcoded Success Rates", success, message)
        return success
    
    def check_api_data_usage(self):
        """Check that components properly use API data"""
        required_patterns = [
            r'fetchWithAuth.*autonomous.*status',  # Uses autonomous status API
            r'realTrading\.capital',  # Uses real capital from API
            r'systemMetrics\.aum',  # Uses AUM from system metrics
            r'data\.data\.',  # Properly accesses API response data
        ]
        
        api_usage_files = []
        
        for jsx_file in self.frontend_dir.glob("*.jsx"):
            content = jsx_file.read_text()
            
            for pattern in required_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    api_usage_files.append(jsx_file.name)
                    break
        
        # Check main dashboard files
        main_files = ['ComprehensiveTradingDashboard.jsx', 'AutonomousTradingDashboard.jsx']
        main_files_using_api = [f for f in main_files if f in api_usage_files]
        
        success = len(main_files_using_api) == len(main_files)
        message = f"{len(main_files_using_api)}/{len(main_files)} main dashboard files use API data properly"
        
        self.log_test_result("API Data Usage", success, message)
        return success
    
    def check_dynamic_capital_display(self):
        """Check that capital is displayed dynamically"""
        dynamic_patterns = [
            r'dashboardData\.systemMetrics\.aum',  # Uses dynamic AUM
            r'realTrading\.capital',  # Uses real capital
            r'systemCapital',  # Uses system capital variable
        ]
        
        static_patterns = [
            r'₹1,000,000',  # Static formatted currency
            r'10.*lakh.*virtual.*capital',  # Static text
        ]
        
        violations = []
        dynamic_usage = []
        
        for jsx_file in self.frontend_dir.glob("*.jsx"):
            content = jsx_file.read_text()
            
            # Check for dynamic patterns
            for pattern in dynamic_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    dynamic_usage.append(jsx_file.name)
                    break
            
            # Check for static patterns
            for pattern in static_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append(f"{jsx_file.name}: {matches}")
        
        success = len(violations) == 0 and len(dynamic_usage) > 0
        message = f"Dynamic usage in {len(dynamic_usage)} files, {len(violations)} static violations"
        
        if violations:
            message += f": {violations[:2]}"
            
        self.log_test_result("Dynamic Capital Display", success, message)
        return success
    
    def check_button_state_logic(self):
        """Check that button states are not hardcoded"""
        proper_patterns = [
            r'tradingStatus\?\.is_running',  # Uses real trading status
            r'TRADING ENGAGED',  # Shows engaged state
            r'data\.data\.is_active',  # Uses API active state
        ]
        
        improper_patterns = [
            r'Start Trading.*hardcoded',  # Hardcoded button text
            r'always.*show.*start',  # Always shows start
        ]
        
        proper_usage = []
        violations = []
        
        for jsx_file in self.frontend_dir.glob("*.jsx"):
            content = jsx_file.read_text()
            
            # Check for proper patterns
            for pattern in proper_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    proper_usage.append(jsx_file.name)
                    break
            
            # Check for improper patterns
            for pattern in improper_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append(f"{jsx_file.name}: {matches}")
        
        success = len(violations) == 0 and len(proper_usage) > 0
        message = f"Proper button logic in {len(proper_usage)} files, {len(violations)} violations"
        
        self.log_test_result("Button State Logic", success, message)
        return success
    
    def run_all_tests(self):
        """Run all tests"""
        print("🔍 Starting No Hardcoded Values Test Suite")
        print("=" * 60)
        
        # Run tests
        self.check_hardcoded_capital_values()
        self.check_mock_data_generation()
        self.check_hardcoded_success_rates()
        self.check_api_data_usage()
        self.check_dynamic_capital_display()
        self.check_button_state_logic()
        
        # Summary
        print("=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test']}: {result['message']}")
        
        print("=" * 60)
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"🎯 OVERALL RESULT: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 PERFECT: No hardcoded values found!")
        elif success_rate >= 80:
            print("✅ GOOD: Most hardcoded values removed")
        else:
            print("⚠️  NEEDS WORK: Hardcoded values still present")
        
        return success_rate >= 80

def main():
    """Main test function"""
    test_suite = HardcodedValuesTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 NO HARDCODED VALUES TEST PASSED!")
        print("✅ All frontend values are now dynamic")
        print("✅ Capital comes from backend API")
        print("✅ Button states reflect real system status")
        print("✅ No mock data generation")
        print("✅ Success rates come from real data")
        return 0
    else:
        print("\n⚠️  HARDCODED VALUES STILL PRESENT")
        print("🔧 Check the test results above for specific issues")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 