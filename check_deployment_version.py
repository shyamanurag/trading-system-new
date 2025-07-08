#!/usr/bin/env python3
"""
Check deployed app version and git commit hash
"""

import requests
import json

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def check_deployment_version():
    """Check the deployed app version"""
    print("🔍 CHECKING DEPLOYED APP VERSION")
    print("=" * 50)
    
    try:
        # Check API info endpoint
        response = requests.get(f"{BASE_URL}/api", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Status: {data.get('status', 'Unknown')}")
            print(f"📦 Version: {data.get('version', 'Unknown')}")
            print(f"🏷️  Name: {data.get('name', 'Unknown')}")
            
            # Check if there's any git info
            if 'git_commit' in data:
                print(f"🔗 Git Commit: {data['git_commit']}")
            if 'build_time' in data:
                print(f"⏰ Build Time: {data['build_time']}")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
        # Check health endpoint for more info
        print("\n" + "=" * 50)
        print("🏥 CHECKING HEALTH ENDPOINT")
        
        health_response = requests.get(f"{BASE_URL}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Health Status: {health_data.get('status', 'Unknown')}")
            
            if 'deployment_info' in health_data:
                deploy_info = health_data['deployment_info']
                print(f"🚀 Deployment Info:")
                for key, value in deploy_info.items():
                    print(f"   • {key}: {value}")
                    
        else:
            print(f"❌ Health endpoint: {health_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    print("🚀 DEPLOYMENT VERSION CHECKER")
    print(f"Testing: {BASE_URL}")
    print()
    
    check_deployment_version()
    
    print("\n" + "=" * 50)
    print("💡 LOCAL GIT INFO:")
    
    # Show local git info for comparison
    import subprocess
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        print(f"🔗 Local Commit: {commit_hash[:8]}")
        
        commit_msg = subprocess.check_output(['git', 'log', '-1', '--pretty=%s']).decode().strip()
        print(f"📝 Last Commit: {commit_msg}")
        
    except Exception as e:
        print(f"❌ Git info error: {e}")

if __name__ == "__main__":
    main() 