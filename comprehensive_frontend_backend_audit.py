#!/usr/bin/env python3
"""
Comprehensive Frontend-Backend Integration Audit

This script identifies all broken frontend-backend connections by:
1. Scanning frontend API calls
2. Testing backend endpoints
3. Checking data format mismatches
4. Identifying missing routes
5. Validating authentication flows
"""

import requests
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append('src')

class FrontendBackendAuditor:
    def __init__(self):
        self.base_url = "https://algoauto-9gx56.ondigitalocean.app"
        self.frontend_path = Path("src/frontend")
        self.backend_path = Path("src/api")
        self.issues = []
        self.working_endpoints = []
        self.broken_endpoints = []
        
    def log_issue(self, severity, component, issue, details=""):
        """Log an integration issue"""
        self.issues.append({
            'severity': severity,
            'component': component,
            'issue': issue,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def scan_frontend_api_calls(self):
        """Scan frontend files for API endpoint calls"""
        print("🔍 Step 1: Scanning frontend API calls...")
        
        api_calls = []
        
        # Common patterns for API calls
        patterns = [
            r'fetchWithAuth\([\'"]([^\'"]+)[\'"]',
            r'fetch\([\'"]([^\'"]+)[\'"]',
            r'axios\.get\([\'"]([^\'"]+)[\'"]',
            r'axios\.post\([\'"]([^\'"]+)[\'"]',
            r'createEndpoint\([\'"]([^\'"]+)[\'"]',
            r'API_ENDPOINTS\.[\w_]+.*[\'"]([^\'"]+)[\'"]',
            r'/api/[^\s\'"]+',
        ]
        
        for js_file in self.frontend_path.rglob("*.js"):
            if js_file.exists():
                try:
                    content = js_file.read_text(encoding='utf-8')
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if match.startswith('/api/') or match.startswith('http'):
                                api_calls.append({
                                    'file': str(js_file),
                                    'endpoint': match,
                                    'line': self.find_line_number(content, match)
                                })
                except Exception as e:
                    self.log_issue('WARNING', 'Frontend', f'Could not read {js_file}', str(e))
        
        for jsx_file in self.frontend_path.rglob("*.jsx"):
            if jsx_file.exists():
                try:
                    content = jsx_file.read_text(encoding='utf-8')
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if match.startswith('/api/') or match.startswith('http'):
                                api_calls.append({
                                    'file': str(jsx_file),
                                    'endpoint': match,
                                    'line': self.find_line_number(content, match)
                                })
                except Exception as e:
                    self.log_issue('WARNING', 'Frontend', f'Could not read {jsx_file}', str(e))
        
        # Remove duplicates
        unique_endpoints = list(set([call['endpoint'] for call in api_calls]))
        print(f"   Found {len(unique_endpoints)} unique API endpoints in frontend")
        
        return api_calls, unique_endpoints
    
    def find_line_number(self, content, search_text):
        """Find line number of text in content"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 0
    
    def test_backend_endpoints(self, endpoints):
        """Test each backend endpoint"""
        print("\n🧪 Step 2: Testing backend endpoints...")
        
        for endpoint in endpoints:
            if not endpoint.startswith('/api/'):
                continue
                
            full_url = f"{self.base_url}{endpoint}"
            
            try:
                # Test GET request
                response = requests.get(full_url, timeout=10)
                
                if response.status_code == 200:
                    self.working_endpoints.append({
                        'endpoint': endpoint,
                        'status': 200,
                        'response_size': len(response.content),
                        'content_type': response.headers.get('content-type', 'unknown')
                    })
                    print(f"   ✅ {endpoint} - Status: {response.status_code}")
                    
                elif response.status_code == 404:
                    self.broken_endpoints.append({
                        'endpoint': endpoint,
                        'status': 404,
                        'error': 'Not Found'
                    })
                    print(f"   ❌ {endpoint} - Status: 404 (Not Found)")
                    self.log_issue('ERROR', 'Backend', f'Endpoint not found: {endpoint}')
                    
                elif response.status_code == 500:
                    self.broken_endpoints.append({
                        'endpoint': endpoint,
                        'status': 500,
                        'error': 'Internal Server Error'
                    })
                    print(f"   ❌ {endpoint} - Status: 500 (Server Error)")
                    self.log_issue('ERROR', 'Backend', f'Server error: {endpoint}')
                    
                else:
                    self.broken_endpoints.append({
                        'endpoint': endpoint,
                        'status': response.status_code,
                        'error': f'HTTP {response.status_code}'
                    })
                    print(f"   ⚠️  {endpoint} - Status: {response.status_code}")
                    self.log_issue('WARNING', 'Backend', f'Unexpected status {response.status_code}: {endpoint}')
                    
            except requests.exceptions.Timeout:
                self.broken_endpoints.append({
                    'endpoint': endpoint,
                    'status': 'timeout',
                    'error': 'Request timeout'
                })
                print(f"   ❌ {endpoint} - Timeout")
                self.log_issue('ERROR', 'Backend', f'Timeout: {endpoint}')
                
            except requests.exceptions.ConnectionError:
                self.broken_endpoints.append({
                    'endpoint': endpoint,
                    'status': 'connection_error',
                    'error': 'Connection failed'
                })
                print(f"   ❌ {endpoint} - Connection Error")
                self.log_issue('ERROR', 'Backend', f'Connection error: {endpoint}')
                
            except Exception as e:
                self.broken_endpoints.append({
                    'endpoint': endpoint,
                    'status': 'error',
                    'error': str(e)
                })
                print(f"   ❌ {endpoint} - Error: {e}")
                self.log_issue('ERROR', 'Backend', f'Error testing {endpoint}', str(e))
    
    def check_api_config(self):
        """Check API configuration files"""
        print("\n⚙️ Step 3: Checking API configuration...")
        
        config_files = [
            'src/frontend/api/config.js',
            'src/frontend/api/api.js',
            'src/frontend/config/realtime.js'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Check for hardcoded URLs
                    if 'localhost' in content:
                        self.log_issue('WARNING', 'Config', f'Hardcoded localhost in {config_file}')
                        print(f"   ⚠️  {config_file} contains hardcoded localhost")
                        
                    # Check for missing environment variables
                    if 'VITE_API_URL' not in content and 'import.meta.env' not in content:
                        self.log_issue('WARNING', 'Config', f'Missing environment variable usage in {config_file}')
                        print(f"   ⚠️  {config_file} may not use environment variables")
                        
                    print(f"   ✅ {config_file} checked")
                    
                except Exception as e:
                    self.log_issue('ERROR', 'Config', f'Could not read {config_file}', str(e))
                    print(f"   ❌ {config_file} - Error: {e}")
            else:
                self.log_issue('ERROR', 'Config', f'Missing config file: {config_file}')
                print(f"   ❌ {config_file} - File not found")
    
    def check_authentication_flow(self):
        """Check authentication endpoints specifically"""
        print("\n🔐 Step 4: Checking authentication flow...")
        
        auth_endpoints = [
            '/auth/zerodha/auth-url',
            '/auth/zerodha/status',
            '/auth/zerodha/submit-token',
            '/auth/zerodha/test-connection',
            '/auth/zerodha/logout',
            '/api/v1/system/status'
        ]
        
        for endpoint in auth_endpoints:
            full_url = f"{self.base_url}{endpoint}"
            
            try:
                if endpoint == '/auth/zerodha/status':
                    # Test with user_id parameter
                    response = requests.get(full_url, params={'user_id': 'PAPER_TRADER_001'}, timeout=10)
                else:
                    response = requests.get(full_url, timeout=10)
                
                if response.status_code == 200:
                    print(f"   ✅ {endpoint} - Working")
                    try:
                        data = response.json()
                        if 'authenticated' in data:
                            print(f"      Auth Status: {data.get('authenticated', 'Unknown')}")
                        if 'user_id' in data:
                            print(f"      User ID: {data.get('user_id', 'Unknown')}")
                    except:
                        pass
                else:
                    print(f"   ❌ {endpoint} - Status: {response.status_code}")
                    self.log_issue('ERROR', 'Authentication', f'Auth endpoint failed: {endpoint}')
                    
            except Exception as e:
                print(f"   ❌ {endpoint} - Error: {e}")
                self.log_issue('ERROR', 'Authentication', f'Auth endpoint error: {endpoint}', str(e))
    
    def check_data_format_consistency(self):
        """Check if frontend expects data in format backend provides"""
        print("\n📊 Step 5: Checking data format consistency...")
        
        # Test some key endpoints for data format
        test_endpoints = [
            '/api/v1/system/status',
            '/api/v1/autonomous/status',
            '/api/v1/trades',
            '/api/v1/positions',
            '/api/v1/strategies'
        ]
        
        for endpoint in test_endpoints:
            full_url = f"{self.base_url}{endpoint}"
            
            try:
                response = requests.get(full_url, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Check common format issues
                        if isinstance(data, dict):
                            if 'success' in data and 'data' in data:
                                print(f"   ✅ {endpoint} - Standard format (success/data)")
                            elif 'error' in data:
                                print(f"   ⚠️  {endpoint} - Error response format")
                            else:
                                print(f"   ⚠️  {endpoint} - Non-standard format")
                                self.log_issue('WARNING', 'Data Format', f'Non-standard response format: {endpoint}')
                        else:
                            print(f"   ⚠️  {endpoint} - Non-object response")
                            self.log_issue('WARNING', 'Data Format', f'Non-object response: {endpoint}')
                            
                    except json.JSONDecodeError:
                        print(f"   ❌ {endpoint} - Invalid JSON")
                        self.log_issue('ERROR', 'Data Format', f'Invalid JSON response: {endpoint}')
                        
                else:
                    print(f"   ❌ {endpoint} - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {endpoint} - Error: {e}")
    
    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n📋 Step 6: Generating comprehensive report...")
        
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_endpoints_found': len(self.working_endpoints) + len(self.broken_endpoints),
                'working_endpoints': len(self.working_endpoints),
                'broken_endpoints': len(self.broken_endpoints),
                'total_issues': len(self.issues),
                'critical_issues': len([i for i in self.issues if i['severity'] == 'ERROR']),
                'warning_issues': len([i for i in self.issues if i['severity'] == 'WARNING'])
            },
            'working_endpoints': self.working_endpoints,
            'broken_endpoints': self.broken_endpoints,
            'issues': self.issues
        }
        
        # Save report
        with open('frontend_backend_audit_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 AUDIT SUMMARY:")
        print(f"   Total Endpoints: {report['summary']['total_endpoints_found']}")
        print(f"   ✅ Working: {report['summary']['working_endpoints']}")
        print(f"   ❌ Broken: {report['summary']['broken_endpoints']}")
        print(f"   🚨 Critical Issues: {report['summary']['critical_issues']}")
        print(f"   ⚠️  Warnings: {report['summary']['warning_issues']}")
        
        print(f"\n🔥 TOP CRITICAL ISSUES:")
        critical_issues = [i for i in self.issues if i['severity'] == 'ERROR'][:10]
        for i, issue in enumerate(critical_issues, 1):
            print(f"   {i}. {issue['component']}: {issue['issue']}")
        
        print(f"\n📄 Full report saved to: frontend_backend_audit_report.json")
        
        return report
    
    def run_audit(self):
        """Run complete audit"""
        print("🔍 COMPREHENSIVE FRONTEND-BACKEND INTEGRATION AUDIT")
        print("=" * 60)
        
        # Step 1: Scan frontend API calls
        api_calls, unique_endpoints = self.scan_frontend_api_calls()
        
        # Step 2: Test backend endpoints
        self.test_backend_endpoints(unique_endpoints)
        
        # Step 3: Check API configuration
        self.check_api_config()
        
        # Step 4: Check authentication flow
        self.check_authentication_flow()
        
        # Step 5: Check data format consistency
        self.check_data_format_consistency()
        
        # Step 6: Generate report
        report = self.generate_report()
        
        print("\n🚀 RECOMMENDED ACTIONS:")
        if report['summary']['broken_endpoints'] > 0:
            print("   1. Fix broken endpoints (404/500 errors)")
        if report['summary']['critical_issues'] > 0:
            print("   2. Address critical integration issues")
        if report['summary']['warning_issues'] > 0:
            print("   3. Review and fix warning issues")
        
        print("\n✅ Audit complete!")
        return report

if __name__ == "__main__":
    auditor = FrontendBackendAuditor()
    auditor.run_audit() 