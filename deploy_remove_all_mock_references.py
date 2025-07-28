#!/usr/bin/env python3
"""
Remove All Mock References Deployment
=====================================

This script removes all mock_mode and sandbox_mode references from the codebase
to ensure the system operates in real trading mode only.

Key Changes:
1. Remove mock_mode from Zerodha client
2. Remove sandbox_mode from configuration  
3. Remove all mock checks and fallbacks
4. Ensure Zerodha analytics fetches real orders
5. Force real trading mode throughout

CRITICAL: This enables REAL MONEY TRADING
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"   Stdout: {e.stdout}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")
        return False

def main():
    print("=" * 60)
    print("🚨 REMOVING ALL MOCK REFERENCES - ENABLING REAL TRADING")
    print("=" * 60)
    print(f"🕐 Deployment started at: {datetime.now()}")
    print()
    
    print("📋 CHANGES BEING DEPLOYED:")
    print("   ✅ Removed mock_mode from Zerodha client")
    print("   ✅ Removed sandbox_mode from configuration")
    print("   ✅ Removed all mock checks and fallbacks")
    print("   ✅ Enhanced Zerodha analytics order fetching")
    print("   ✅ Force real trading mode throughout system")
    print()
    
    print("⚠️  CRITICAL WARNING:")
    print("   🔴 This deployment enables REAL MONEY TRADING")
    print("   💰 All orders will use actual funds")
    print("   📊 Analytics will fetch real Zerodha data")
    print()
    
    # Git operations
    commands = [
        ("git add .", "Adding all changes to git"),
        ("git commit -m 'CRITICAL: Remove all mock references - Enable real trading mode\n\n- Remove mock_mode from Zerodha client and all components\n- Remove sandbox_mode from configuration files\n- Remove all mock checks and fallbacks\n- Enhanced order fetching with better date filtering\n- Force real trading mode throughout system\n- Fix Zerodha analytics to fetch actual orders\n\nREAL MONEY TRADING ENABLED'", "Committing changes"),
        ("git push origin main", "Pushing to trigger deployment")
    ]
    
    success_count = 0
    for command, description in commands:
        if run_command(command, description):
            success_count += 1
        else:
            print(f"\n❌ Deployment failed at: {description}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎯 MOCK REMOVAL DEPLOYMENT COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"✅ All {success_count} operations completed successfully")
    print(f"🕐 Deployment completed at: {datetime.now()}")
    print()
    print("📊 EXPECTED RESULTS:")
    print("   🔴 System operates in REAL TRADING mode only")
    print("   📋 Zerodha analytics fetches actual orders")
    print("   💰 Dashboard shows real trade data")
    print("   🚫 No more mock mode references")
    print()
    print("🔍 NEXT STEPS:")
    print("   1. Wait for DigitalOcean deployment to complete")
    print("   2. Check dashboard for real order data")
    print("   3. Verify 2 executed orders appear in analytics")
    print("   4. Confirm position sync works correctly")
    print()
    print("⚠️  REMINDER: REAL MONEY TRADING IS NOW ACTIVE")

if __name__ == "__main__":
    main() 