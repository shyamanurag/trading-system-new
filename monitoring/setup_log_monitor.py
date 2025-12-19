"""
Setup Script for DigitalOcean Log Monitor

This script helps you configure the environment variables needed
for the log monitor to fetch logs directly from DigitalOcean.

Run this once to set up your credentials.
"""

import os
import sys
from pathlib import Path

def setup():
    print("=" * 60)
    print("🔧 DigitalOcean Log Monitor Setup")
    print("=" * 60)
    print()
    
    print("This will help you configure the log monitor.")
    print("You'll need:")
    print("  1. A DigitalOcean API Token (with read access)")
    print("  2. Your App ID from the DigitalOcean dashboard")
    print()
    
    # Check if already configured
    existing_token = os.getenv("DO_API_TOKEN")
    existing_app_id = os.getenv("DO_APP_ID")
    
    if existing_token and existing_app_id:
        print("✅ Already configured!")
        print(f"   Token: {existing_token[:10]}...{existing_token[-5:]}")
        print(f"   App ID: {existing_app_id}")
        print()
        reconfigure = input("Do you want to reconfigure? (y/n): ").strip().lower()
        if reconfigure != 'y':
            return
    
    print()
    print("Step 1: Get your DigitalOcean API Token")
    print("   1. Go to: https://cloud.digitalocean.com/account/api/tokens")
    print("   2. Click 'Generate New Token'")
    print("   3. Give it a name (e.g., 'AlgoAuto Log Monitor')")
    print("   4. Select 'Read' scope")
    print("   5. Copy the token")
    print()
    
    api_token = input("Paste your API Token: ").strip()
    
    if not api_token:
        print("❌ No token provided. Exiting.")
        return
    
    print()
    print("Step 2: Get your App ID")
    print("   1. Go to your app in DigitalOcean App Platform")
    print("   2. Look at the URL - it contains the App ID")
    print("   3. Example: cloud.digitalocean.com/apps/abc123-xyz")
    print("      The App ID is: abc123-xyz")
    print()
    print("   OR provide your app URL like: algoauto-9gx56.ondigitalocean.app")
    print()
    
    app_id = input("Enter App ID or URL: ").strip()
    
    if not app_id:
        print("❌ No App ID provided. Exiting.")
        return
    
    # Create .env file content
    env_content = f"""
# DigitalOcean Log Monitor Configuration
# Added by setup_log_monitor.py

DO_API_TOKEN={api_token}
DO_APP_ID={app_id}
"""
    
    # Find env file location
    project_root = Path(__file__).parent.parent
    env_file = project_root / "config" / "production.env"
    
    # Check if production.env exists
    if env_file.exists():
        print()
        print(f"Found existing env file: {env_file}")
        append = input("Append to this file? (y/n): ").strip().lower()
        
        if append == 'y':
            with open(env_file, 'a') as f:
                f.write(env_content)
            print(f"✅ Added credentials to {env_file}")
        else:
            # Create new file
            new_env_file = project_root / ".env.logmonitor"
            with open(new_env_file, 'w') as f:
                f.write(env_content.strip())
            print(f"✅ Created new file: {new_env_file}")
            print("   Add these to your deployment environment variables.")
    else:
        # Create .env file in root
        env_file = project_root / ".env"
        if env_file.exists():
            with open(env_file, 'a') as f:
                f.write(env_content)
            print(f"✅ Added credentials to {env_file}")
        else:
            with open(env_file, 'w') as f:
                f.write(env_content.strip())
            print(f"✅ Created {env_file}")
    
    print()
    print("=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print()
    print("For local testing, run:")
    print("  python monitoring/digitalocean_log_monitor.py")
    print()
    print("For production, add these to your DigitalOcean App:")
    print("  1. Go to your app Settings")
    print("  2. Click 'App-Level Environment Variables'")
    print("  3. Add:")
    print(f"     DO_API_TOKEN = {api_token[:10]}...")
    print(f"     DO_APP_ID = {app_id}")
    print()
    print("API Endpoints available after deployment:")
    print("  GET /api/v1/logs/health   - Get health report")
    print("  GET /api/v1/logs/recent   - Get recent logs")
    print("  GET /api/v1/logs/analyze  - Analyze logs for issues")
    print("  GET /api/v1/logs/errors   - Get only error logs")
    print("  GET /api/v1/logs/search?pattern=xxx - Search logs")


if __name__ == "__main__":
    setup()
