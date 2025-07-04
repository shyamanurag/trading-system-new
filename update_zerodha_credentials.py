#!/usr/bin/env python3
"""
Update Zerodha API Credentials
Updates the new API key and secret in configuration files
"""

import os
import re

# Current active credentials (confirmed working)
NEW_API_KEY = "vc9ft4zpknynpm3u"
NEW_API_SECRET = "0nwjb2cncw9stf3m5cre73rqc3bc5xsc"

# Old credentials to replace (if any exist)
OLD_API_KEY = "sylcoq492qz6f7ej"
OLD_API_SECRET = "jm3h4iejwnxr4ngmma2qxccpkhevo8sy"

def update_file(filepath, old_key, new_key, old_secret, new_secret):
    """Update credentials in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace API key
        content = content.replace(old_key, new_key)
        # Replace API secret
        content = content.replace(old_secret, new_secret)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return False

# Files to update
files_to_update = [
    "src/api/zerodha_manual_auth.py",
    "src/api/zerodha_auth.py",
    "config/production.env.example",
    ".env"  # If exists
]

print("🔐 Updating Zerodha Credentials")
print("=" * 40)
print(f"New API Key: {NEW_API_KEY}")
print(f"New API Secret: {NEW_API_SECRET[:10]}...")
print()

updated_count = 0
for filepath in files_to_update:
    if os.path.exists(filepath):
        print(f"Updating: {filepath}")
        if update_file(filepath, OLD_API_KEY, NEW_API_KEY, OLD_API_SECRET, NEW_API_SECRET):
            updated_count += 1
            print(f"✓ Updated successfully")
        else:
            print(f"✗ Failed to update")
    else:
        print(f"⏭️ Skipping (not found): {filepath}")

print(f"\n✅ Updated {updated_count} files")

# Create a new environment file with the credentials
print("\n📝 Creating new environment configuration...")

env_content = f"""# Zerodha API Configuration
ZERODHA_API_KEY={NEW_API_KEY}
ZERODHA_API_SECRET={NEW_API_SECRET}
ZERODHA_USER_ID=QSW899

# Note: Update these in DigitalOcean App Platform environment variables
"""

with open("zerodha_credentials.env", "w") as f:
    f.write(env_content)

print("✓ Created zerodha_credentials.env")

# Generate the new authorization URL
auth_url = f"https://kite.zerodha.com/connect/login?api_key={NEW_API_KEY}"

print("\n🔗 New Authorization URL:")
print(auth_url)
print("\n📋 Next Steps:")
print("1. Update environment variables in DigitalOcean App Platform:")
print(f"   ZERODHA_API_KEY={NEW_API_KEY}")
print(f"   ZERODHA_API_SECRET={NEW_API_SECRET}")
print("\n2. Visit the authorization URL above")
print("3. Login to Zerodha")
print("4. Copy the request_token from the redirect URL")
print("5. Submit at: https://algoauto-9gx56.ondigitalocean.app/auth/zerodha/")

print("\n✅ Script completed!") 