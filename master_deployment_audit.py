#!/usr/bin/env python3
"""
🚀 MASTER DEPLOYMENT AUDIT
=========================

Comprehensive audit of your DigitalOcean trading app deployment.
This script provides a complete health check and actionable recommendations.
"""

import sys
import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MasterAuditor:
    """Master deployment auditor"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = None
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def audit_deployment_health(self) -> Dict:
        """Audit deployment health"""
        logger.info("🔍 Auditing Deployment Health...")
        
        health_checks = {}
        
        # Basic connectivity
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                health_checks["basic_connectivity"] = response.status == 200
                if response.status == 200:
                    data = await response.json()
                    health_checks["health_endpoint_data"] = data
        except Exception as e:
            health_checks["basic_connectivity"] = False
            health_checks["connectivity_error"] = str(e)
        
        # System health
        try:
            async with self.session.get(f"{self.base_url}/health/ready/json") as response:
                if response.status == 200:
                    data = await response.json()
                    health_checks["system_ready"] = data.get("ready", False)
                    health_checks["database_connected"] = data.get("database_connected", False)
                    health_checks["redis_connected"] = data.get("redis_connected", False)
                    health_checks["trading_enabled"] = data.get("trading_enabled", False)
                else:
                    health_checks["system_ready"] = False
        except Exception as e:
            health_checks["system_ready"] = False
            health_checks["system_error"] = str(e)
        
        return health_checks
    
    async def audit_frontend(self) -> Dict:
        """Audit frontend functionality"""
        logger.info("🌐 Auditing Frontend...")
        
        frontend_checks = {}
        
        # Homepage loading
        try:
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    content = await response.text()
                    frontend_checks["homepage_loads"] = True
                    frontend_checks["has_html"] = "<!DOCTYPE html>" in content
                    frontend_checks["reasonable_size"] = len(content) > 1000
                    frontend_checks["has_trading_content"] = "trading" in content.lower()
                else:
                    frontend_checks["homepage_loads"] = False
                    frontend_checks["status_code"] = response.status
        except Exception as e:
            frontend_checks["homepage_loads"] = False
            frontend_checks["error"] = str(e)
        
        # API Documentation
        try:
            async with self.session.get(f"{self.base_url}/docs") as response:
                frontend_checks["docs_available"] = response.status == 200
        except:
            frontend_checks["docs_available"] = False
        
        return frontend_checks
    
    async def audit_zerodha_auth(self) -> Dict:
        """Audit Zerodha authentication"""
        logger.info("🔐 Auditing Zerodha Authentication...")
        
        auth_checks = {}
        
        # Main auth page
        try:
            async with self.session.get(f"{self.base_url}/zerodha") as response:
                if response.status == 200:
                    content = await response.text()
                    auth_checks["auth_page_loads"] = True
                    auth_checks["has_zerodha_content"] = "zerodha" in content.lower()
                    auth_checks["has_auth_form"] = any(word in content.lower() for word in ["login", "token", "authenticate"])
                else:
                    auth_checks["auth_page_loads"] = False
        except Exception as e:
            auth_checks["auth_page_loads"] = False
            auth_checks["error"] = str(e)
        
        # Auth status endpoint
        try:
            async with self.session.get(f"{self.base_url}/zerodha/status") as response:
                auth_checks["auth_status_endpoint"] = response.status in [200, 401]
        except:
            auth_checks["auth_status_endpoint"] = False
        
        # Manual auth URL endpoint
        try:
            async with self.session.get(f"{self.base_url}/auth/zerodha/auth-url") as response:
                if response.status == 200:
                    data = await response.json()
                    auth_checks["manual_auth_available"] = True
                    auth_checks["generates_kite_url"] = "kite.zerodha.com" in str(data)
                else:
                    auth_checks["manual_auth_available"] = False
        except:
            auth_checks["manual_auth_available"] = False
        
        return auth_checks
    
    async def audit_api_endpoints(self) -> Dict:
        """Audit API endpoints"""
        logger.info("🔌 Auditing API Endpoints...")
        
        endpoints_to_test = [
            ("/api", "API Root"),
            ("/api/auth/me", "Auth Status"),
            ("/api/v1/market/indices", "Market Indices"),
            ("/api/v1/monitoring/system-status", "System Status"),
            ("/api/v1/recommendations", "Recommendations")
        ]
        
        api_checks = {}
        working_endpoints = 0
        
        for endpoint, name in endpoints_to_test:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    # Accept various status codes
                    is_working = response.status in [200, 201, 401, 422]
                    api_checks[f"endpoint_{endpoint.replace('/', '_')}"] = {
                        "working": is_working,
                        "status_code": response.status,
                        "name": name
                    }
                    if is_working:
                        working_endpoints += 1
            except Exception as e:
                api_checks[f"endpoint_{endpoint.replace('/', '_')}"] = {
                    "working": False,
                    "error": str(e),
                    "name": name
                }
        
        api_checks["working_endpoints_count"] = working_endpoints
        api_checks["total_endpoints_tested"] = len(endpoints_to_test)
        api_checks["success_rate"] = (working_endpoints / len(endpoints_to_test)) * 100
        
        return api_checks
    
    def generate_recommendations(self, audit_results: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check deployment health
        if not audit_results["deployment_health"].get("basic_connectivity", False):
            recommendations.append("🚨 CRITICAL: App is not reachable - check DigitalOcean deployment status")
        
        if not audit_results["deployment_health"].get("system_ready", False):
            recommendations.append("⚠️ System health check failing - check application logs")
        
        if not audit_results["deployment_health"].get("database_connected", False):
            recommendations.append("🗄️ Database connection issues - verify database configuration")
        
        if not audit_results["deployment_health"].get("redis_connected", False):
            recommendations.append("🔴 Redis connection issues - check Redis service status")
        
        # Check frontend
        if not audit_results["frontend"].get("homepage_loads", False):
            recommendations.append("🌐 Frontend not loading - check static file serving")
        
        # Check Zerodha auth
        if not audit_results["zerodha_auth"].get("auth_page_loads", False):
            recommendations.append("🔐 Zerodha auth page not loading - check authentication routes")
        
        if not audit_results["zerodha_auth"].get("has_zerodha_content", False):
            recommendations.append("📝 Zerodha auth page missing proper content - check auth templates")
        
        if not audit_results["zerodha_auth"].get("manual_auth_available", False):
            recommendations.append("🔧 Manual Zerodha auth not working - check API endpoint configuration")
        
        # Check API endpoints
        success_rate = audit_results["api_endpoints"].get("success_rate", 0)
        if success_rate < 70:
            recommendations.append("🔌 Many API endpoints failing - check route configuration and dependencies")
        
        # If no issues found
        if not recommendations:
            recommendations.append("✅ System appears healthy - continue monitoring")
        
        return recommendations
    
    def calculate_overall_score(self, audit_results: Dict) -> float:
        """Calculate overall health score"""
        scores = []
        
        # Deployment health (40% weight)
        deployment_score = 0
        if audit_results["deployment_health"].get("basic_connectivity", False):
            deployment_score += 25
        if audit_results["deployment_health"].get("system_ready", False):
            deployment_score += 25
        if audit_results["deployment_health"].get("database_connected", False):
            deployment_score += 25
        if audit_results["deployment_health"].get("redis_connected", False):
            deployment_score += 25
        scores.append(("Deployment Health", deployment_score, 0.4))
        
        # Frontend (20% weight)
        frontend_score = 0
        if audit_results["frontend"].get("homepage_loads", False):
            frontend_score += 50
        if audit_results["frontend"].get("docs_available", False):
            frontend_score += 50
        scores.append(("Frontend", frontend_score, 0.2))
        
        # Zerodha Auth (25% weight)
        auth_score = 0
        if audit_results["zerodha_auth"].get("auth_page_loads", False):
            auth_score += 33
        if audit_results["zerodha_auth"].get("has_zerodha_content", False):
            auth_score += 33
        if audit_results["zerodha_auth"].get("manual_auth_available", False):
            auth_score += 34
        scores.append(("Zerodha Auth", auth_score, 0.25))
        
        # API Endpoints (15% weight)
        api_score = audit_results["api_endpoints"].get("success_rate", 0)
        scores.append(("API Endpoints", api_score, 0.15))
        
        # Calculate weighted average
        weighted_score = sum(score * weight for _, score, weight in scores)
        
        return weighted_score
    
    async def run_complete_audit(self) -> Dict:
        """Run complete audit"""
        logger.info("🚀 Starting Master Deployment Audit")
        logger.info(f"📍 Target: {self.base_url}")
        logger.info("=" * 60)
        
        # Run all audits
        audit_results = {
            "deployment_health": await self.audit_deployment_health(),
            "frontend": await self.audit_frontend(),
            "zerodha_auth": await self.audit_zerodha_auth(),
            "api_endpoints": await self.audit_api_endpoints()
        }
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(audit_results)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(audit_results)
        
        # Determine status
        if overall_score >= 90:
            status = "EXCELLENT 🟢"
        elif overall_score >= 75:
            status = "GOOD 🟡"
        elif overall_score >= 50:
            status = "FAIR 🟠"
        else:
            status = "POOR 🔴"
        
        # Compile final report
        final_report = {
            "audit_metadata": {
                "timestamp": datetime.now().isoformat(),
                "target_url": self.base_url,
                "audit_type": "Master Deployment Audit"
            },
            "overall_assessment": {
                "status": status,
                "score": f"{overall_score:.1f}%",
                "raw_score": overall_score
            },
            "detailed_results": audit_results,
            "recommendations": recommendations
        }
        
        # Print summary
        self.print_audit_summary(final_report)
        
        return final_report
    
    def print_audit_summary(self, report: Dict):
        """Print audit summary"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 MASTER AUDIT SUMMARY")
        logger.info("=" * 60)
        
        overall = report["overall_assessment"]
        logger.info(f"🎯 Overall Status: {overall['status']}")
        logger.info(f"📈 Health Score: {overall['score']}")
        
        # Component breakdown
        logger.info(f"\n📋 Component Status:")
        
        deployment = report["detailed_results"]["deployment_health"]
        logger.info(f"   🚀 Deployment: {'✅' if deployment.get('basic_connectivity', False) else '❌'} {'Connected' if deployment.get('basic_connectivity', False) else 'Issues'}")
        logger.info(f"   🗄️ Database: {'✅' if deployment.get('database_connected', False) else '❌'} {'Connected' if deployment.get('database_connected', False) else 'Issues'}")
        logger.info(f"   🔴 Redis: {'✅' if deployment.get('redis_connected', False) else '❌'} {'Connected' if deployment.get('redis_connected', False) else 'Issues'}")
        
        frontend = report["detailed_results"]["frontend"]
        logger.info(f"   🌐 Frontend: {'✅' if frontend.get('homepage_loads', False) else '❌'} {'Working' if frontend.get('homepage_loads', False) else 'Issues'}")
        
        auth = report["detailed_results"]["zerodha_auth"]
        logger.info(f"   🔐 Zerodha Auth: {'✅' if auth.get('auth_page_loads', False) else '❌'} {'Working' if auth.get('auth_page_loads', False) else 'Issues'}")
        
        api = report["detailed_results"]["api_endpoints"]
        logger.info(f"   🔌 API Endpoints: {api.get('working_endpoints_count', 0)}/{api.get('total_endpoints_tested', 0)} working")
        
        # Recommendations
        logger.info(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(report["recommendations"][:5], 1):
            logger.info(f"   {i}. {rec}")

async def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://algoauto-9gx56.ondigitalocean.app"
    
    print(f"🚀 Master Deployment Audit")
    print(f"📍 Target: {base_url}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with MasterAuditor(base_url) as auditor:
        final_report = await auditor.run_complete_audit()
        
        # Save report
        filename = f"master_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"\n📄 Master audit report saved: {filename}")
        
        # Exit code
        score = final_report["overall_assessment"]["raw_score"]
        return 0 if score >= 70 else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n❌ Audit interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Audit failed: {e}")
        sys.exit(1) 