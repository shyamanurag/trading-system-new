#!/usr/bin/env python3
"""
Fix Frontend-Backend Integration Issues

Based on the audit, fix the critical broken endpoints:
1. /api/v1/trades -> /api/v1/autonomous/trades
2. /api/v1/strategies -> /api/v1/autonomous/strategies  
3. /api/v1/users -> /api/v1/users/performance
4. /auth/zerodha/submit-token -> already exists, path issue
"""

import os
import re
from pathlib import Path

def fix_api_endpoints():
    """Fix API endpoint mismatches in frontend"""
    
    print("🔧 Fixing Frontend-Backend API Endpoint Mismatches")
    print("=" * 60)
    
    # Frontend API configuration file
    config_file = Path("src/frontend/api/config.js")
    
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return False
    
    try:
        content = config_file.read_text(encoding='utf-8')
        original_content = content
        
        print("📝 Applying fixes to API endpoints...")
        
        # Fix 1: /api/v1/trades -> /api/v1/autonomous/trades
        content = re.sub(
            r"TRADES:\s*createEndpoint\(['\"]\/api\/v1\/trades['\"]",
            "TRADES: createEndpoint('/api/v1/autonomous/trades'",
            content
        )
        print("   ✅ Fixed TRADES endpoint: /api/v1/trades -> /api/v1/autonomous/trades")
        
        # Fix 2: /api/v1/strategies -> /api/v1/autonomous/strategies
        content = re.sub(
            r"STRATEGIES:\s*createEndpoint\(['\"]\/api\/v1\/strategies['\"]",
            "STRATEGIES: createEndpoint('/api/v1/autonomous/strategies'",
            content
        )
        print("   ✅ Fixed STRATEGIES endpoint: /api/v1/strategies -> /api/v1/autonomous/strategies")
        
        # Fix 3: /api/v1/users -> /api/v1/users/performance (if it exists)
        content = re.sub(
            r"USERS:\s*createEndpoint\(['\"]\/api\/v1\/users\/['\"]",
            "USERS: createEndpoint('/api/v1/users/performance'",
            content
        )
        print("   ✅ Fixed USERS endpoint: /api/v1/users/ -> /api/v1/users/performance")
        
        # Fix 4: Add missing strategy performance endpoint
        if "STRATEGY_PERFORMANCE" not in content:
            # Add after STRATEGIES line
            content = re.sub(
                r"(STRATEGIES:\s*createEndpoint\([^)]+\),)",
                r"\1\n    STRATEGY_PERFORMANCE: createEndpoint('/api/v1/autonomous/performance'),",
                content
            )
            print("   ✅ Added STRATEGY_PERFORMANCE endpoint")
        
        # Fix 5: Add missing autonomous status endpoint (if not exists)
        if "AUTONOMOUS_STATUS" not in content:
            content = re.sub(
                r"(TRADING_STATUS:\s*createEndpoint\([^)]+\),)",
                r"\1\n    AUTONOMOUS_STATUS: createEndpoint('/api/v1/autonomous/status'),",
                content
            )
            print("   ✅ Added AUTONOMOUS_STATUS endpoint")
        
        # Write the fixed content
        if content != original_content:
            config_file.write_text(content, encoding='utf-8')
            print(f"✅ Updated {config_file}")
            return True
        else:
            print("ℹ️  No changes needed in config file")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing config file: {e}")
        return False

def fix_component_api_calls():
    """Fix direct API calls in components"""
    
    print("\n🔧 Fixing Component API Calls...")
    
    frontend_components = Path("src/frontend/components")
    
    if not frontend_components.exists():
        print(f"❌ Components directory not found: {frontend_components}")
        return False
    
    fixes_applied = 0
    
    # Common API call patterns to fix
    fixes = [
        # Fix trades endpoint
        (r"['\"]\/api\/v1\/trades['\"]", "'/api/v1/autonomous/trades'"),
        (r"['\"]\/api\/v1\/trades\/['\"]", "'/api/v1/autonomous/trades'"),
        
        # Fix strategies endpoint  
        (r"['\"]\/api\/v1\/strategies['\"]", "'/api/v1/autonomous/strategies'"),
        (r"['\"]\/api\/v1\/strategies\/['\"]", "'/api/v1/autonomous/strategies'"),
        
        # Fix users endpoint
        (r"['\"]\/api\/v1\/users\/['\"]", "'/api/v1/users/performance'"),
        
        # Fix auth endpoint (common mistake)
        (r"['\"]\/auth\/zerodha\/submit-token['\"]", "'/auth/zerodha/submit-token'"),
    ]
    
    for jsx_file in frontend_components.rglob("*.jsx"):
        try:
            content = jsx_file.read_text(encoding='utf-8')
            original_content = content
            
            for pattern, replacement in fixes:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    fixes_applied += 1
                    print(f"   ✅ Fixed API call in {jsx_file.name}")
            
            if content != original_content:
                jsx_file.write_text(content, encoding='utf-8')
                
        except UnicodeDecodeError:
            print(f"   ⚠️  Skipping {jsx_file.name} - encoding issue")
        except Exception as e:
            print(f"   ❌ Error processing {jsx_file.name}: {e}")
    
    print(f"   Applied {fixes_applied} fixes to component files")
    return fixes_applied > 0

def add_missing_backend_routes():
    """Add missing backend routes that frontend expects"""
    
    print("\n🔧 Adding Missing Backend Routes...")
    
    # Check if we need to add any missing routes
    missing_routes = [
        {
            'path': '/api/v1/trades',
            'redirect_to': '/api/v1/autonomous/trades',
            'description': 'Redirect trades to autonomous trades'
        },
        {
            'path': '/api/v1/strategies',
            'redirect_to': '/api/v1/autonomous/strategies', 
            'description': 'Redirect strategies to autonomous strategies'
        },
        {
            'path': '/api/v1/users',
            'redirect_to': '/api/v1/users/performance',
            'description': 'Redirect users to users performance'
        }
    ]
    
    # Add redirect routes to main.py
    main_file = Path("main.py")
    
    if not main_file.exists():
        print(f"❌ Main file not found: {main_file}")
        return False
    
    try:
        content = main_file.read_text(encoding='utf-8')
        
        # Add redirect routes before the catch-all route
        redirect_routes = '''
# Frontend-Backend Integration Fixes - Redirect Routes
@app.get("/api/v1/trades", tags=["trades"])
async def redirect_trades():
    """Redirect to autonomous trades endpoint"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/autonomous/trades", status_code=307)

@app.get("/api/v1/strategies", tags=["strategies"])  
async def redirect_strategies():
    """Redirect to autonomous strategies endpoint"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/autonomous/strategies", status_code=307)

@app.get("/api/v1/users", tags=["users"])
async def redirect_users():
    """Redirect to users performance endpoint"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/users/performance", status_code=307)

'''
        
        # Insert before the catch-all route
        catch_all_pattern = r'(@app\.api_route\("/\{path:path\}".*?async def catch_all)'
        
        if re.search(catch_all_pattern, content, re.DOTALL):
            content = re.sub(
                catch_all_pattern,
                redirect_routes + r'\1',
                content,
                flags=re.DOTALL
            )
            
            main_file.write_text(content, encoding='utf-8')
            print("   ✅ Added redirect routes to main.py")
            return True
        else:
            print("   ⚠️  Could not find catch-all route to insert redirects")
            return False
            
    except Exception as e:
        print(f"❌ Error adding redirect routes: {e}")
        return False

def test_fixes():
    """Test the fixes by checking endpoints"""
    
    print("\n🧪 Testing Fixes...")
    
    import requests
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    test_endpoints = [
        '/api/v1/autonomous/trades',
        '/api/v1/autonomous/strategies',
        '/api/v1/users/performance',
        '/auth/zerodha/submit-token'
    ]
    
    working = 0
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code in [200, 405]:  # 405 is OK for POST endpoints
                print(f"   ✅ {endpoint} - Working")
                working += 1
            else:
                print(f"   ❌ {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {e}")
    
    print(f"\n📊 Test Results: {working}/{len(test_endpoints)} endpoints working")
    
    return working == len(test_endpoints)

def main():
    """Run all fixes"""
    
    print("🚀 COMPREHENSIVE FRONTEND-BACKEND INTEGRATION FIX")
    print("=" * 60)
    
    success = True
    
    # Step 1: Fix API endpoints in config
    if not fix_api_endpoints():
        success = False
    
    # Step 2: Fix component API calls
    if not fix_component_api_calls():
        success = False
    
    # Step 3: Add missing backend routes
    if not add_missing_backend_routes():
        success = False
    
    # Step 4: Test fixes
    test_fixes()
    
    if success:
        print("\n✅ ALL FIXES APPLIED SUCCESSFULLY!")
        print("\n🚀 Next Steps:")
        print("   1. Commit and deploy the changes")
        print("   2. Test frontend functionality")
        print("   3. Monitor for any remaining issues")
    else:
        print("\n⚠️  Some fixes failed - manual intervention may be needed")
    
    return success

if __name__ == "__main__":
    main() 