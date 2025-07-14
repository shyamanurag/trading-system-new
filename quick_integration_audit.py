#!/usr/bin/env python3
"""
Quick Frontend-Backend Integration Audit

Focus on the most critical integration issues
"""

import requests
import json
import re
from pathlib import Path

def quick_audit():
    print("🔍 QUICK FRONTEND-BACKEND INTEGRATION AUDIT")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Critical endpoints that frontend likely uses
    critical_endpoints = [
        '/api/v1/system/status',
        '/api/v1/autonomous/status', 
        '/api/v1/trades',
        '/api/v1/positions',
        '/api/v1/orders',
        '/api/v1/strategies',
        '/api/v1/users',
        '/api/v1/dashboard/summary',
        '/api/v1/elite',
        '/auth/zerodha/status',
        '/auth/zerodha/auth-url',
        '/auth/zerodha/submit-token'
    ]
    
    working = []
    broken = []
    
    print("\n🧪 Testing Critical Endpoints:")
    
    for endpoint in critical_endpoints:
        full_url = f"{base_url}{endpoint}"
        
        try:
            if endpoint == '/auth/zerodha/status':
                response = requests.get(full_url, params={'user_id': 'PAPER_TRADER_001'}, timeout=5)
            else:
                response = requests.get(full_url, timeout=5)
            
            if response.status_code == 200:
                working.append(endpoint)
                print(f"   ✅ {endpoint}")
            elif response.status_code == 404:
                broken.append({'endpoint': endpoint, 'error': '404 Not Found'})
                print(f"   ❌ {endpoint} - 404 Not Found")
            elif response.status_code == 500:
                broken.append({'endpoint': endpoint, 'error': '500 Server Error'})
                print(f"   ❌ {endpoint} - 500 Server Error")
            else:
                broken.append({'endpoint': endpoint, 'error': f'HTTP {response.status_code}'})
                print(f"   ⚠️  {endpoint} - {response.status_code}")
                
        except requests.exceptions.Timeout:
            broken.append({'endpoint': endpoint, 'error': 'Timeout'})
            print(f"   ❌ {endpoint} - Timeout")
        except Exception as e:
            broken.append({'endpoint': endpoint, 'error': str(e)})
            print(f"   ❌ {endpoint} - {str(e)[:50]}...")
    
    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Working: {len(working)}")
    print(f"   ❌ Broken: {len(broken)}")
    
    if broken:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in broken:
            print(f"   - {issue['endpoint']}: {issue['error']}")
    
    # Quick frontend API config check
    print(f"\n⚙️ Checking Frontend API Config:")
    
    config_files = [
        'src/frontend/api/config.js',
        'src/frontend/api/api.js'
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            try:
                content = Path(config_file).read_text()
                if 'localhost' in content:
                    print(f"   ⚠️  {config_file} has hardcoded localhost")
                else:
                    print(f"   ✅ {config_file} looks good")
            except Exception as e:
                print(f"   ❌ {config_file} - Error: {e}")
        else:
            print(f"   ❌ {config_file} - Not found")
    
    # Check for common frontend patterns
    print(f"\n🔍 Checking Frontend API Usage:")
    
    frontend_path = Path("src/frontend")
    if frontend_path.exists():
        api_patterns = []
        
        for jsx_file in frontend_path.rglob("*.jsx"):
            try:
                content = jsx_file.read_text()
                
                # Look for API calls
                api_calls = re.findall(r'/api/[^\s\'"]+', content)
                for call in api_calls:
                    if call not in api_patterns:
                        api_patterns.append(call)
                        
            except Exception as e:
                print(f"   ⚠️  Could not read {jsx_file}: {e}")
        
        print(f"   Found {len(api_patterns)} unique API patterns in frontend")
        
        # Check if critical patterns are working
        for pattern in api_patterns[:10]:  # Check first 10
            if pattern in [ep for ep in working]:
                print(f"   ✅ {pattern} - Working")
            elif any(pattern == b['endpoint'] for b in broken):
                print(f"   ❌ {pattern} - Broken")
            else:
                print(f"   ❓ {pattern} - Unknown")
    
    print(f"\n🎯 IMMEDIATE ACTIONS NEEDED:")
    
    if len(broken) > len(working):
        print("   🚨 CRITICAL: More endpoints broken than working!")
        print("   1. Fix broken endpoints immediately")
        print("   2. Check backend routing configuration")
        print("   3. Verify deployment status")
    
    if any('404' in b['error'] for b in broken):
        print("   📍 Multiple 404 errors - check route definitions")
    
    if any('500' in b['error'] for b in broken):
        print("   💥 Server errors - check backend logs")
    
    if any('Timeout' in b['error'] for b in broken):
        print("   ⏱️  Timeout issues - check server performance")
    
    print(f"\n✅ Quick audit complete!")
    return working, broken

if __name__ == "__main__":
    quick_audit() 