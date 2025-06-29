#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE ZERODHA AUTHENTICATION AUDIT
==============================================

This script performs a thorough audit of the Zerodha authentication system,
identifying connection issues, configuration problems, and implementation flaws.
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
    
    async def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run the complete audit"""
        logger.info("🚀 Starting Comprehensive Zerodha Authentication Audit")
        logger.info("=" * 60)
        
        # Run all tests
        tests = [
            ("Kiteconnect Import", self.test_kiteconnect_import()),
            ("Environment Variables", self.test_environment_variables()),
            ("Redis Connection", self.test_redis_connection()),
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