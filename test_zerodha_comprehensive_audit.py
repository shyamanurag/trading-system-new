#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE ZERODHA AUTHENTICATION AUDIT
==============================================

This script performs a thorough audit of the Zerodha authentication system,
identifying connection issues, configuration problems, and implementation flaws.

Author: AI Trading System Auditor
Date: December 2024
"""

import os
import sys
import asyncio
import logging
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZerodhaAudit:
    """Comprehensive Zerodha authentication audit"""
    
    def __init__(self):
        self.issues = []
        self.fixes = []
        self.test_results = {}
        
    def log_issue(self, category: str, issue: str, severity: str = "MEDIUM"):
        """Log an issue found during audit"""
        self.issues.append({
            "category": category,
            "issue": issue,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
        logger.error(f"🚨 {severity} - {category}: {issue}")
    
    def log_fix(self, issue: str, fix: str):
        """Log a recommended fix"""
        self.fixes.append({
            "issue": issue,
            "fix": fix,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"💡 FIX: {issue} -> {fix}")
    
    async def test_kiteconnect_import(self):
        """Test if kiteconnect library can be imported"""
        logger.info("🔍 Testing kiteconnect library import...")
        try:
            import kiteconnect
            from kiteconnect import KiteConnect, KiteTicker
            logger.info("✅ kiteconnect library imported successfully")
            self.test_results['kiteconnect_import'] = True
            return True
        except ImportError as e:
            self.log_issue("DEPENDENCIES", f"kiteconnect library not installed: {e}", "CRITICAL")
            self.log_fix("Missing kiteconnect", "Run: pip install kiteconnect")
            self.test_results['kiteconnect_import'] = False
            return False
    
    def test_environment_variables(self):
        """Test if required environment variables are set"""
        logger.info("🔍 Testing environment variables...")
        required_vars = [
            'ZERODHA_API_KEY',
            'ZERODHA_API_SECRET', 
            'ZERODHA_USER_ID',
            'REDIS_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                self.log_issue("CONFIG", f"Environment variable {var} not set", "HIGH")
        
        if missing_vars:
            self.log_fix("Missing env vars", f"Set environment variables: {', '.join(missing_vars)}")
            self.test_results['env_vars'] = False
            return False
        else:
            logger.info("✅ All required environment variables are set")
            self.test_results['env_vars'] = True
            return True
    
    async def test_redis_connection(self):
        """Test Redis connection for token storage"""
        logger.info("🔍 Testing Redis connection...")
        try:
            import redis.asyncio as redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            redis_client = await redis.from_url(redis_url)
            
            # Test basic Redis operations
            await redis_client.set("test_key", "test_value")
            result = await redis_client.get("test_key")
            await redis_client.delete("test_key")
            await redis_client.close()
            
            if result and result.decode() == "test_value":
                logger.info("✅ Redis connection successful")
                self.test_results['redis'] = True
                return True
            else:
                self.log_issue("REDIS", "Redis test operation failed", "HIGH")
                self.test_results['redis'] = False
                return False
                
        except Exception as e:
            self.log_issue("REDIS", f"Redis connection failed: {e}", "HIGH")
            self.log_fix("Redis connection", "Check REDIS_URL and Redis server status")
            self.test_results['redis'] = False
            return False
    
    def test_auth_file_conflicts(self):
        """Test for conflicting authentication files"""
        logger.info("🔍 Testing for authentication file conflicts...")
        
        auth_files = [
            'src/api/zerodha_auth.py',
            'src/api/zerodha_daily_auth.py',
            'src/api/zerodha_manual_auth.py',
            'src/api/zerodha_multi_user_auth.py'
        ]
        
        existing_files = []
        for file_path in auth_files:
            if os.path.exists(file_path):
                existing_files.append(file_path)
        
        if len(existing_files) > 2:
            self.log_issue("ARCHITECTURE", 
                         f"Multiple auth files detected: {existing_files}. This can cause conflicts.", 
                         "MEDIUM")
            self.log_fix("Multiple auth files", 
                        "Consolidate authentication logic into a single, well-structured module")
        
        logger.info(f"Found {len(existing_files)} authentication files")
        self.test_results['auth_files'] = len(existing_files)
        return len(existing_files) <= 2
    
    async def test_zerodha_auth_initialization(self):
        """Test Zerodha authentication initialization"""
        logger.info("🔍 Testing Zerodha authentication initialization...")
        
        if not self.test_results.get('kiteconnect_import', False):
            self.log_issue("AUTH", "Cannot test auth - kiteconnect not available", "HIGH")
            return False
        
        try:
            from kiteconnect import KiteConnect
            api_key = os.getenv('ZERODHA_API_KEY')
            
            if not api_key:
                self.log_issue("AUTH", "ZERODHA_API_KEY not available for testing", "HIGH")
                return False
            
            # Test KiteConnect initialization
            kite = KiteConnect(api_key=api_key)
            login_url = kite.login_url()
            
            if login_url and "kite.zerodha.com" in login_url:
                logger.info("✅ Zerodha KiteConnect initialization successful")
                logger.info(f"Login URL generated: {login_url[:50]}...")
                self.test_results['zerodha_init'] = True
                return True
            else:
                self.log_issue("AUTH", "Invalid login URL generated", "MEDIUM")
                self.test_results['zerodha_init'] = False
                return False
                
        except Exception as e:
            self.log_issue("AUTH", f"Zerodha auth initialization failed: {e}", "HIGH")
            self.test_results['zerodha_init'] = False
            return False
    
    def test_mock_vs_real_confusion(self):
        """Test for mock mode vs real implementation confusion"""
        logger.info("🔍 Testing for mock vs real implementation issues...")
        
        # Check brokers/zerodha.py for mock mode confusion
        mock_issues = []
        
        try:
            with open('brokers/zerodha.py', 'r') as f:
                content = f.read()
                if 'mock_mode = config.get(\'mock_mode\', True)' in content:
                    mock_issues.append("Mock mode defaults to True in brokers/zerodha.py")
                if 'NO MOCK DATA - Real Zerodha data required' in content:
                    mock_issues.append("Conflicting mock/real data comments")
        except FileNotFoundError:
            pass
        
        # Check core zerodha files
        try:
            with open('src/core/zerodha.py', 'r') as f:
                content = f.read()
                if 'mock' in content.lower():
                    mock_issues.append("Mock references found in core zerodha implementation")
        except FileNotFoundError:
            pass
        
        if mock_issues:
            for issue in mock_issues:
                self.log_issue("IMPLEMENTATION", issue, "MEDIUM")
            self.log_fix("Mock confusion", "Clearly separate mock and real implementations")
            return False
        else:
            logger.info("✅ No obvious mock/real implementation conflicts")
            return True
    
    def analyze_token_management(self):
        """Analyze token management implementation"""
        logger.info("🔍 Analyzing token management...")
        
        issues_found = []
        
        # Check for consistent token key naming
        token_patterns = []
        auth_files = [
            'src/api/zerodha_daily_auth.py',
            'src/api/zerodha_multi_user_auth.py',
            'src/core/zerodha.py'
        ]
        
        for file_path in auth_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Look for token key patterns
                    if 'zerodha:token:' in content:
                        token_patterns.append(f"{file_path}: zerodha:token:")
                    if 'zerodha:multi:token:' in content:
                        token_patterns.append(f"{file_path}: zerodha:multi:token:")
                    if 'zerodha:' in content and 'access_token' in content:
                        token_patterns.append(f"{file_path}: zerodha:*:access_token")
                        
            except FileNotFoundError:
                continue
        
        if len(set([p.split(':')[1] for p in token_patterns])) > 1:
            issues_found.append("Inconsistent token key naming patterns")
            self.log_issue("TOKEN_MGMT", "Inconsistent Redis token key patterns", "MEDIUM")
        
        # Check for token expiry management
        expiry_management = False
        for file_path in auth_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'token_expiry' in content and 'datetime' in content:
                        expiry_management = True
                        break
            except FileNotFoundError:
                continue
        
        if not expiry_management:
            issues_found.append("No proper token expiry management found")
            self.log_issue("TOKEN_MGMT", "Missing token expiry management", "HIGH")
        
        if not issues_found:
            logger.info("✅ Token management appears well-structured")
            return True
        else:
            self.log_fix("Token management", "Implement consistent token key naming and expiry management")
            return False
    
    def test_websocket_implementation(self):
        """Test WebSocket implementation for issues"""
        logger.info("🔍 Testing WebSocket implementation...")
        
        try:
            with open('src/core/zerodha.py', 'r') as f:
                content = f.read()
                
                # Check for WebSocket initialization
                if 'KiteTicker' not in content:
                    self.log_issue("WEBSOCKET", "KiteTicker not properly imported", "HIGH")
                    return False
                
                # Check for proper callback handling
                callbacks = ['on_ticks', 'on_connect', 'on_close', 'on_error']
                missing_callbacks = []
                for callback in callbacks:
                    if callback not in content:
                        missing_callbacks.append(callback)
                
                if missing_callbacks:
                    self.log_issue("WEBSOCKET", 
                                 f"Missing WebSocket callbacks: {missing_callbacks}", "MEDIUM")
                    self.log_fix("WebSocket callbacks", "Implement all required WebSocket event handlers")
                
                # Check for connection state management
                if 'ticker_connected' not in content:
                    self.log_issue("WEBSOCKET", "No WebSocket connection state tracking", "MEDIUM")
                
                logger.info("✅ WebSocket implementation structure looks reasonable")
                return True
                
        except FileNotFoundError:
            self.log_issue("WEBSOCKET", "Core Zerodha file not found", "CRITICAL")
            return False
    
    def check_api_route_conflicts(self):
        """Check for API route conflicts"""
        logger.info("🔍 Checking for API route conflicts...")
        
        routes_found = {}
        auth_files = [
            ('src/api/zerodha_auth.py', '/api/zerodha'),
            ('src/api/zerodha_daily_auth.py', '/zerodha'),
            ('src/api/zerodha_manual_auth.py', '/auth/zerodha'),
            ('src/api/zerodha_multi_user_auth.py', '/zerodha-multi')
        ]
        
        conflicts = []
        for file_path, prefix in auth_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Extract route definitions
                    import re
                    route_patterns = re.findall(r'@router\.(get|post|put|delete)\("([^"]+)"', content)
                    
                    for method, route in route_patterns:
                        full_route = f"{method.upper()} {prefix}{route}"
                        if full_route in routes_found:
                            conflicts.append(f"Route conflict: {full_route} in {file_path} and {routes_found[full_route]}")
                        else:
                            routes_found[full_route] = file_path
                            
            except FileNotFoundError:
                continue
        
        if conflicts:
            for conflict in conflicts:
                self.log_issue("ROUTES", conflict, "HIGH")
            self.log_fix("Route conflicts", "Consolidate or rename conflicting routes")
            return False
        else:
            logger.info("✅ No obvious API route conflicts found")
            return True
    
    async def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run the complete audit"""
        logger.info("🚀 Starting Comprehensive Zerodha Authentication Audit")
        logger.info("=" * 60)
        
        # Run all tests
        tests = [
            ("Kiteconnect Import", self.test_kiteconnect_import()),
            ("Environment Variables", self.test_environment_variables()),
            ("Redis Connection", self.test_redis_connection()),
            ("Auth File Conflicts", self.test_auth_file_conflicts()),
            ("Zerodha Auth Init", self.test_zerodha_auth_initialization()),
            ("Mock vs Real", self.test_mock_vs_real_confusion()),
            ("Token Management", self.analyze_token_management()),
            ("WebSocket Implementation", self.test_websocket_implementation()),
            ("API Route Conflicts", self.check_api_route_conflicts())
        ]
        
        results = {}
        for test_name, test_coro in tests:
            logger.info(f"\n🔍 Running: {test_name}")
            try:
                if asyncio.iscoroutine(test_coro):
                    result = await test_coro
                else:
                    result = test_coro
                results[test_name] = result
                logger.info(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                logger.error(f"❌ {test_name} crashed: {e}")
                results[test_name] = False
        
        # Generate audit report
        report = {
            "audit_timestamp": datetime.now().isoformat(),
            "test_results": results,
            "issues_found": self.issues,
            "recommended_fixes": self.fixes,
            "summary": {
                "total_tests": len(tests),
                "passed_tests": sum(1 for r in results.values() if r),
                "failed_tests": sum(1 for r in results.values() if not r),
                "critical_issues": len([i for i in self.issues if i['severity'] == 'CRITICAL']),
                "high_issues": len([i for i in self.issues if i['severity'] == 'HIGH']),
                "medium_issues": len([i for i in self.issues if i['severity'] == 'MEDIUM'])
            }
        }
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 AUDIT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Tests Passed: {report['summary']['passed_tests']}/{report['summary']['total_tests']}")
        logger.info(f"Critical Issues: {report['summary']['critical_issues']}")
        logger.info(f"High Priority Issues: {report['summary']['high_issues']}")  
        logger.info(f"Medium Priority Issues: {report['summary']['medium_issues']}")
        
        if report['summary']['critical_issues'] > 0:
            logger.error("🚨 CRITICAL ISSUES FOUND - System may not work properly")
        elif report['summary']['high_issues'] > 0:
            logger.warning("⚠️ HIGH PRIORITY ISSUES FOUND - Functionality may be limited")
        elif report['summary']['medium_issues'] > 0:
            logger.info("💡 MEDIUM PRIORITY ISSUES FOUND - Consider addressing for better reliability")
        else:
            logger.info("✅ NO MAJOR ISSUES FOUND - System appears healthy")
        
        return report

async def main():
    """Main audit function"""
    auditor = ZerodhaAudit()
    report = await auditor.run_comprehensive_audit()
    
    # Save report to file
    with open('zerodha_audit_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\n📄 Full audit report saved to: zerodha_audit_report.json")
    
    return report

if __name__ == "__main__":
    asyncio.run(main()) 