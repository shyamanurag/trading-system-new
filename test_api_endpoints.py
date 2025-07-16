#!/usr/bin/env python3
"""
Test API Endpoints - Verify routing configuration
This script tests that all API endpoints are properly registered and accessible.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_api_routes():
    """Test that API routes are properly configured"""
    print("🔍 Testing API Route Configuration")
    print("=" * 50)
    
    try:
        # Import the main application
        from bootstrap import app
        
        # Get all routes from the FastAPI app
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method != 'HEAD':  # Skip HEAD methods
                        routes.append(f"{method} {route.path}")
        
        # Sort routes for better readability
        routes.sort()
        
        print(f"✅ Found {len(routes)} API routes")
        print("\n📋 All Available Routes:")
        print("-" * 50)
        
        # Check for our specific endpoints
        dynamic_user_routes = []
        analytics_routes = []
        
        for route in routes:
            print(f"   {route}")
            if '/api/v1/users/dynamic' in route:
                dynamic_user_routes.append(route)
            if '/api/v1/analytics' in route:
                analytics_routes.append(route)
        
        print("\n🎯 Dynamic User Management Routes:")
        if dynamic_user_routes:
            for route in dynamic_user_routes:
                print(f"   ✅ {route}")
        else:
            print("   ❌ No dynamic user management routes found!")
        
        print("\n📊 Analytics Routes:")
        if analytics_routes:
            for route in analytics_routes:
                print(f"   ✅ {route}")
        else:
            print("   ❌ No analytics routes found!")
        
        # Check for the specific route that was reported as missing
        target_route = "GET /api/v1/users/dynamic/list"
        if target_route in routes:
            print(f"\n✅ Target route found: {target_route}")
        else:
            print(f"\n❌ Target route MISSING: {target_route}")
            print("   Available dynamic user routes:")
            for route in dynamic_user_routes:
                print(f"      {route}")
        
        return len(dynamic_user_routes) > 0 and len(analytics_routes) > 0
        
    except Exception as e:
        print(f"❌ Error testing API routes: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 API Endpoint Configuration Test")
    print("=" * 50)
    
    success = test_api_routes()
    
    if success:
        print("\n✅ API endpoints are properly configured!")
    else:
        print("\n❌ API endpoint configuration issues found.")
        print("\n🔧 Troubleshooting Steps:")
        print("   1. Check that routers are added to router_imports in main.py")
        print("   2. Check that routers are added to router_configs for mounting")
        print("   3. Remove any duplicate router registrations")
        print("   4. Restart the application after making changes")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 