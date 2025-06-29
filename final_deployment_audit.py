#!/usr/bin/env python3
"""
🚀 FINAL DEPLOYMENT AUDIT
========================

Comprehensive audit of your DigitalOcean deployment with actionable insights.
"""

import sys
import requests
import json
from datetime import datetime

def test_deployment(base_url):
    """Run comprehensive deployment test"""
    print(f"🚀 COMPREHENSIVE DEPLOYMENT AUDIT")
    print(f"📍 Target: {base_url}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Basic Connectivity
    print("\n🔍 Testing Basic Connectivity...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ App is reachable")
            results["connectivity"] = True
            health_data = response.json()
            results["health_data"] = health_data
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            results["connectivity"] = False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        results["connectivity"] = False
    
    # Test 2: System Health
    print("\n🔍 Testing System Health...")
    try:
        response = requests.get(f"{base_url}/health/ready/json", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            db_connected = health_data.get("database_connected", False)
            redis_connected = health_data.get("redis_connected", False)
            trading_enabled = health_data.get("trading_enabled", False)
            
            print(f"📊 Database: {'✅ Connected' if db_connected else '❌ Issues'}")
            print(f"🔴 Redis: {'✅ Connected' if redis_connected else '❌ Issues'}")
            print(f"💰 Trading: {'✅ Enabled' if trading_enabled else '❌ Disabled'}")
            
            results["system_health"] = {
                "database": db_connected,
                "redis": redis_connected,
                "trading": trading_enabled
            }
        else:
            print(f"❌ System health check failed: {response.status_code}")
            results["system_health"] = False
    except Exception as e:
        print(f"❌ System health check failed: {e}")
        results["system_health"] = False
    
    # Test 3: Frontend
    print("\n🔍 Testing Frontend...")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            content = response.text
            has_html = "<!DOCTYPE html>" in content
            has_react = "react" in content.lower() or "vite" in content.lower()
            reasonable_size = len(content) > 1000
            
            print(f"🌐 Homepage: {'✅ Loads' if has_html else '❌ Issues'}")
            print(f"⚛️ React/Vite: {'✅ Detected' if has_react else '❌ Not found'}")
            print(f"📏 Content Size: {'✅ Good' if reasonable_size else '❌ Too small'}")
            
            results["frontend"] = {
                "loads": has_html,
                "has_framework": has_react,
                "good_size": reasonable_size
            }
        else:
            print(f"❌ Frontend failed: {response.status_code}")
            results["frontend"] = False
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        results["frontend"] = False
    
    # Test 4: Zerodha Authentication
    print("\n🔍 Testing Zerodha Authentication...")
    auth_score = 0
    total_auth_tests = 3
    
    # Test auth page
    try:
        response = requests.get(f"{base_url}/zerodha", timeout=10)
        if response.status_code == 200:
            content = response.text.lower()
            if "zerodha" in content and "login" in content:
                print("✅ Zerodha auth page working")
                auth_score += 1
            else:
                print("⚠️ Zerodha auth page missing content")
        else:
            print(f"❌ Zerodha auth page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Zerodha auth page failed: {e}")
    
    # Test auth status
    try:
        response = requests.get(f"{base_url}/zerodha/status", timeout=10)
        if response.status_code in [200, 401]:
            print("✅ Zerodha auth status endpoint working")
            auth_score += 1
        else:
            print(f"❌ Auth status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Auth status test failed: {e}")
    
    # Test manual auth
    try:
        response = requests.get(f"{base_url}/auth/zerodha/auth-url", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "kite.zerodha.com" in str(data):
                print("✅ Manual auth URL generation working")
                auth_score += 1
            else:
                print("⚠️ Manual auth URL incomplete")
        else:
            print(f"❌ Manual auth failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Manual auth test failed: {e}")
    
    results["zerodha_auth"] = {
        "score": auth_score,
        "total": total_auth_tests,
        "working": auth_score >= 2
    }
    
    # Test 5: API Endpoints
    print("\n🔍 Testing API Endpoints...")
    api_endpoints = [
        ("/api", "API Root"),
        ("/api/auth/me", "Auth Status"),
        ("/health/ready/json", "Health JSON")
    ]
    
    working_apis = 0
    for endpoint, name in api_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code in [200, 401]:
                print(f"✅ {name}: Working")
                working_apis += 1
            else:
                print(f"❌ {name}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Failed - {e}")
    
    results["api_endpoints"] = {
        "working": working_apis,
        "total": len(api_endpoints)
    }
    
    # Calculate Overall Score
    print("\n" + "=" * 60)
    print("📊 AUDIT SUMMARY")
    print("=" * 60)
    
    score_components = []
    
    # Connectivity (25%)
    if results.get("connectivity", False):
        score_components.append(25)
    else:
        score_components.append(0)
    
    # System Health (25%)
    if results.get("system_health", False):
        health = results["system_health"]
        if isinstance(health, dict):
            health_score = sum([health.get("database", False), health.get("redis", False), health.get("trading", False)])
            score_components.append((health_score / 3) * 25)
        else:
            score_components.append(0)
    else:
        score_components.append(0)
    
    # Frontend (20%)
    if results.get("frontend", False):
        frontend = results["frontend"]
        if isinstance(frontend, dict):
            frontend_score = sum([frontend.get("loads", False), frontend.get("has_framework", False), frontend.get("good_size", False)])
            score_components.append((frontend_score / 3) * 20)
        else:
            score_components.append(0)
    else:
        score_components.append(0)
    
    # Zerodha Auth (20%)
    if results.get("zerodha_auth", {}).get("working", False):
        score_components.append(20)
    else:
        score_components.append(0)
    
    # API Endpoints (10%)
    api_data = results.get("api_endpoints", {})
    if api_data.get("working", 0) > 0:
        api_score = (api_data["working"] / api_data["total"]) * 10
        score_components.append(api_score)
    else:
        score_components.append(0)
    
    overall_score = sum(score_components)
    
    # Determine Status
    if overall_score >= 90:
        status = "EXCELLENT 🟢"
    elif overall_score >= 75:
        status = "GOOD 🟡"
    elif overall_score >= 50:
        status = "FAIR 🟠"
    else:
        status = "POOR 🔴"
    
    print(f"🎯 Overall Status: {status}")
    print(f"📈 Health Score: {overall_score:.1f}%")
    
    # Component Status
    print(f"\n📋 Component Status:")
    print(f"   🚀 Connectivity: {'✅ Working' if results.get('connectivity', False) else '❌ Issues'}")
    
    if isinstance(results.get("system_health"), dict):
        health = results["system_health"]
        print(f"   🗄️ Database: {'✅ Connected' if health.get('database', False) else '❌ Issues'}")
        print(f"   🔴 Redis: {'✅ Connected' if health.get('redis', False) else '❌ Issues'}")
        print(f"   💰 Trading: {'✅ Enabled' if health.get('trading', False) else '❌ Disabled'}")
    else:
        print(f"   🏥 System Health: ❌ Issues")
    
    if isinstance(results.get("frontend"), dict):
        print(f"   🌐 Frontend: ✅ Working")
    else:
        print(f"   🌐 Frontend: ❌ Issues")
    
    auth_data = results.get("zerodha_auth", {})
    print(f"   🔐 Zerodha Auth: {'✅ Working' if auth_data.get('working', False) else '❌ Issues'} ({auth_data.get('score', 0)}/{auth_data.get('total', 3)})")
    
    api_data = results.get("api_endpoints", {})
    print(f"   🔌 API Endpoints: {api_data.get('working', 0)}/{api_data.get('total', 0)} working")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    recommendations = []
    
    if not results.get("connectivity", False):
        recommendations.append("🚨 CRITICAL: Fix app connectivity - check DigitalOcean deployment")
    
    if isinstance(results.get("system_health"), dict):
        health = results["system_health"]
        if not health.get("database", False):
            recommendations.append("🗄️ Fix database connection - check DATABASE_URL")
        if not health.get("redis", False):
            recommendations.append("🔴 Fix Redis connection - check REDIS_URL")
    else:
        recommendations.append("🏥 Fix system health endpoints")
    
    if not isinstance(results.get("frontend"), dict):
        recommendations.append("🌐 Fix frontend loading issues")
    
    if not results.get("zerodha_auth", {}).get("working", False):
        recommendations.append("🔐 Fix Zerodha authentication system")
    
    if api_data.get("working", 0) < api_data.get("total", 1):
        recommendations.append("🔌 Fix failing API endpoints")
    
    if not recommendations:
        recommendations.append("✅ System is healthy - continue monitoring")
    
    for i, rec in enumerate(recommendations[:5], 1):
        print(f"   {i}. {rec}")
    
    # Save Report
    report = {
        "timestamp": datetime.now().isoformat(),
        "target_url": base_url,
        "overall_score": overall_score,
        "status": status,
        "detailed_results": results,
        "recommendations": recommendations
    }
    
    filename = f"deployment_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved: {filename}")
    
    return overall_score >= 70

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://algoauto-9gx56.ondigitalocean.app"
    
    success = test_deployment(base_url)
    
    if success:
        print("\n✅ Deployment audit completed successfully")
        return 0
    else:
        print("\n⚠️ Deployment audit found issues requiring attention")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Audit interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Audit failed: {e}")
        sys.exit(1) 