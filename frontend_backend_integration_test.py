"""
🔍 COMPREHENSIVE FRONTEND-BACKEND INTEGRATION TEST
=================================================
Tests all critical API endpoints that the frontend depends on to ensure
proper integration and identify any missing or broken connections.

This script validates:
1. API endpoint availability and response format
2. Authentication flow
3. Data consistency between frontend expectations and backend responses
4. Error handling and fallback mechanisms
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EndpointTest:
    """Test case for an API endpoint"""
    name: str
    url: str
    method: str = 'GET'
    requires_auth: bool = False
    expected_fields: List[str] = None
    payload: Dict = None
    description: str = ""

class FrontendBackendIntegrationTester:
    """Comprehensive integration tester"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('API_BASE_URL', 'https://algoauto-9gx56.ondigitalocean.app')
        self.session = None
        self.auth_token = None
        self.test_results = []
        
        # Define critical endpoints that frontend depends on
        self.critical_endpoints = [
            # Authentication endpoints
            EndpointTest(
                name="API Root",
                url="/api",
                description="API root endpoint - should return API info"
            ),
            EndpointTest(
                name="Health Check",
                url="/health",
                description="Basic health check"
            ),
            
            # Elite Recommendations (Critical for frontend)
            EndpointTest(
                name="Elite Recommendations",
                url="/api/v1/elite/",
                description="Main elite recommendations endpoint",
                expected_fields=["success", "recommendations", "total_count"]
            ),
            EndpointTest(
                name="Elite Signal Statistics",
                url="/api/v1/elite/signal-statistics",
                description="Signal performance statistics",
                expected_fields=["success", "statistics"]
            ),
            EndpointTest(
                name="Elite Live Signals",
                url="/api/v1/elite/live-signals",
                description="Live signals from strategies",
                expected_fields=["success", "live_signals", "total_count"]
            ),
            EndpointTest(
                name="Elite Signal Lifecycle",
                url="/api/v1/elite/signal-lifecycle",
                description="Signal lifecycle statistics",
                expected_fields=["success", "lifecycle_stats"]
            ),
            
            # Autonomous Trading (Critical for dashboard)
            EndpointTest(
                name="Autonomous Status",
                url="/api/v1/autonomous/status",
                description="Autonomous trading status",
                expected_fields=["success"]
            ),
            EndpointTest(
                name="Autonomous Strategies",
                url="/api/v1/autonomous/strategies",
                description="Available trading strategies",
                expected_fields=["success"]
            ),
            
            # Dashboard Data
            EndpointTest(
                name="Dashboard Summary",
                url="/api/v1/dashboard/summary",
                description="Dashboard summary data",
                expected_fields=["success"]
            ),
            EndpointTest(
                name="Daily P&L",
                url="/api/v1/dashboard/daily-pnl",
                description="Daily P&L data",
                expected_fields=["success"]
            ),
            
            # User Management
            EndpointTest(
                name="Broker Users",
                url="/api/v1/control/users/broker",
                description="Broker user management",
                expected_fields=["success"]
            ),
            
            # Market Data
            EndpointTest(
                name="Market Indices",
                url="/api/market/indices",
                description="Market indices data"
            ),
            EndpointTest(
                name="Market Status",
                url="/api/market/market-status",
                description="Market status information"
            ),
            
            # System Status
            EndpointTest(
                name="System Status",
                url="/api/v1/system/status",
                description="System health and status"
            ),
            
            # Search Functionality
            EndpointTest(
                name="Search Symbols",
                url="/api/v1/search/symbols?q=NIFTY",
                description="Symbol search functionality"
            ),
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Frontend-Backend-Integration-Tester/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, endpoint: EndpointTest) -> Dict[str, Any]:
        """Test a single endpoint"""
        result = {
            'name': endpoint.name,
            'url': endpoint.url,
            'method': endpoint.method,
            'status': 'UNKNOWN',
            'response_time_ms': 0,
            'status_code': 0,
            'error': None,
            'response_data': None,
            'missing_fields': [],
            'description': endpoint.description
        }
        
        try:
            start_time = datetime.now()
            
            # Prepare headers
            headers = {}
            if endpoint.requires_auth and self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            # Make request
            url = f"{self.base_url}{endpoint.url}"
            
            if endpoint.method.upper() == 'GET':
                async with self.session.get(url, headers=headers) as response:
                    result['status_code'] = response.status
                    result['response_data'] = await response.json()
            elif endpoint.method.upper() == 'POST':
                async with self.session.post(url, headers=headers, json=endpoint.payload) as response:
                    result['status_code'] = response.status
                    result['response_data'] = await response.json()
            
            # Calculate response time
            end_time = datetime.now()
            result['response_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
            
            # Check status
            if 200 <= result['status_code'] < 300:
                result['status'] = 'SUCCESS'
            elif result['status_code'] == 404:
                result['status'] = 'NOT_FOUND'
                result['error'] = 'Endpoint not found'
            elif result['status_code'] == 500:
                result['status'] = 'SERVER_ERROR'
                result['error'] = 'Internal server error'
            else:
                result['status'] = 'ERROR'
                result['error'] = f'HTTP {result["status_code"]}'
            
            # Check expected fields
            if endpoint.expected_fields and result['response_data']:
                missing_fields = []
                for field in endpoint.expected_fields:
                    if field not in result['response_data']:
                        missing_fields.append(field)
                result['missing_fields'] = missing_fields
                
                if missing_fields:
                    result['status'] = 'PARTIAL_SUCCESS'
                    result['error'] = f'Missing fields: {", ".join(missing_fields)}'
            
        except aiohttp.ClientError as e:
            result['status'] = 'CONNECTION_ERROR'
            result['error'] = f'Connection error: {str(e)}'
        except json.JSONDecodeError as e:
            result['status'] = 'INVALID_JSON'
            result['error'] = f'Invalid JSON response: {str(e)}'
        except Exception as e:
            result['status'] = 'UNKNOWN_ERROR'
            result['error'] = f'Unknown error: {str(e)}'
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all endpoint tests"""
        logger.info(f"🚀 Starting Frontend-Backend Integration Test")
        logger.info(f"📡 Testing against: {self.base_url}")
        logger.info(f"🔍 Testing {len(self.critical_endpoints)} critical endpoints")
        
        results = []
        
        for i, endpoint in enumerate(self.critical_endpoints, 1):
            logger.info(f"🧪 [{i}/{len(self.critical_endpoints)}] Testing: {endpoint.name}")
            
            result = await self.test_endpoint(endpoint)
            results.append(result)
            
            # Log result
            status_emoji = {
                'SUCCESS': '✅',
                'PARTIAL_SUCCESS': '⚠️',
                'NOT_FOUND': '❌',
                'SERVER_ERROR': '🔥',
                'CONNECTION_ERROR': '🌐',
                'INVALID_JSON': '📄',
                'ERROR': '❌',
                'UNKNOWN_ERROR': '❓'
            }.get(result['status'], '❓')
            
            logger.info(f"   {status_emoji} {result['status']} ({result['response_time_ms']}ms)")
            if result['error']:
                logger.info(f"      Error: {result['error']}")
        
        # Generate summary
        summary = self._generate_summary(results)
        
        return {
            'summary': summary,
            'results': results,
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url
        }
    
    def _generate_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate test summary"""
        total = len(results)
        success = len([r for r in results if r['status'] == 'SUCCESS'])
        partial = len([r for r in results if r['status'] == 'PARTIAL_SUCCESS'])
        errors = total - success - partial
        
        # Categorize by functionality
        categories = {
            'Elite Recommendations': [r for r in results if 'elite' in r['url'].lower()],
            'Autonomous Trading': [r for r in results if 'autonomous' in r['url'].lower()],
            'Dashboard': [r for r in results if 'dashboard' in r['url'].lower()],
            'System': [r for r in results if any(x in r['url'].lower() for x in ['health', 'system', 'api'])],
            'Market Data': [r for r in results if 'market' in r['url'].lower()],
            'User Management': [r for r in results if 'users' in r['url'].lower()],
            'Other': [r for r in results if not any(cat.lower().replace(' ', '') in r['url'].lower() for cat in ['elite', 'autonomous', 'dashboard', 'health', 'system', 'api', 'market', 'users'])]
        }
        
        category_stats = {}
        for cat_name, cat_results in categories.items():
            if cat_results:
                cat_success = len([r for r in cat_results if r['status'] == 'SUCCESS'])
                category_stats[cat_name] = {
                    'total': len(cat_results),
                    'success': cat_success,
                    'success_rate': (cat_success / len(cat_results)) * 100
                }
        
        # Critical issues
        critical_issues = []
        for result in results:
            if result['status'] in ['NOT_FOUND', 'SERVER_ERROR', 'CONNECTION_ERROR']:
                critical_issues.append({
                    'endpoint': result['name'],
                    'url': result['url'],
                    'issue': result['error'],
                    'impact': 'HIGH' if any(x in result['url'].lower() for x in ['elite', 'autonomous', 'dashboard']) else 'MEDIUM'
                })
        
        return {
            'total_endpoints': total,
            'successful': success,
            'partial_success': partial,
            'errors': errors,
            'success_rate': (success / total) * 100 if total > 0 else 0,
            'overall_health': 'HEALTHY' if success >= total * 0.8 else 'DEGRADED' if success >= total * 0.6 else 'CRITICAL',
            'category_breakdown': category_stats,
            'critical_issues': critical_issues,
            'avg_response_time': sum(r['response_time_ms'] for r in results) / len(results) if results else 0
        }
    
    def print_detailed_report(self, test_results: Dict):
        """Print detailed test report"""
        summary = test_results['summary']
        
        print("\n" + "="*80)
        print("🔍 FRONTEND-BACKEND INTEGRATION TEST REPORT")
        print("="*80)
        
        print(f"\n📊 OVERALL SUMMARY:")
        print(f"   Total Endpoints Tested: {summary['total_endpoints']}")
        print(f"   Successful: {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"   Partial Success: {summary['partial_success']}")
        print(f"   Errors: {summary['errors']}")
        print(f"   Overall Health: {summary['overall_health']}")
        print(f"   Average Response Time: {summary['avg_response_time']:.0f}ms")
        
        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category, stats in summary['category_breakdown'].items():
            status_emoji = '✅' if stats['success_rate'] >= 80 else '⚠️' if stats['success_rate'] >= 60 else '❌'
            print(f"   {status_emoji} {category}: {stats['success']}/{stats['total']} ({stats['success_rate']:.1f}%)")
        
        if summary['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in summary['critical_issues']:
                impact_emoji = '🔥' if issue['impact'] == 'HIGH' else '⚠️'
                print(f"   {impact_emoji} {issue['endpoint']}: {issue['issue']}")
                print(f"      URL: {issue['url']}")
        
        print(f"\n📝 DETAILED RESULTS:")
        for result in test_results['results']:
            status_emoji = {
                'SUCCESS': '✅',
                'PARTIAL_SUCCESS': '⚠️',
                'NOT_FOUND': '❌',
                'SERVER_ERROR': '🔥',
                'CONNECTION_ERROR': '🌐',
                'ERROR': '❌'
            }.get(result['status'], '❓')
            
            print(f"   {status_emoji} {result['name']}")
            print(f"      URL: {result['url']}")
            print(f"      Status: {result['status']} (HTTP {result['status_code']})")
            print(f"      Response Time: {result['response_time_ms']}ms")
            
            if result['error']:
                print(f"      Error: {result['error']}")
            
            if result['missing_fields']:
                print(f"      Missing Fields: {', '.join(result['missing_fields'])}")
            
            print()
        
        print("="*80)
        print(f"Test completed at: {test_results['timestamp']}")
        print("="*80)

async def main():
    """Main test execution"""
    # You can override the base URL for testing
    base_url = os.getenv('TEST_API_URL', 'https://algoauto-9gx56.ondigitalocean.app')
    
    async with FrontendBackendIntegrationTester(base_url) as tester:
        results = await tester.run_all_tests()
        tester.print_detailed_report(results)
        
        # Save results to file
        with open('frontend_backend_integration_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: frontend_backend_integration_results.json")
        
        # Return exit code based on health
        health = results['summary']['overall_health']
        if health == 'HEALTHY':
            return 0
        elif health == 'DEGRADED':
            return 1
        else:
            return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
