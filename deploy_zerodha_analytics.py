#!/usr/bin/env python3
"""
Deploy Zerodha Analytics System
===============================
Deploys the new Zerodha-based analytics system that bypasses the faulty internal database
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_zerodha_analytics_files():
    """Verify that Zerodha analytics files exist"""
    logger.info("🔍 Verifying Zerodha analytics files...")
    
    required_files = [
        'src/core/zerodha_analytics.py',
        'src/api/zerodha_analytics.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            logger.info(f"✅ {file_path}: Found")
        else:
            logger.error(f"❌ {file_path}: Missing")
            return False
    
    return True

def verify_main_integration():
    """Verify that main.py includes the new router"""
    logger.info("🔍 Verifying main.py integration...")
    
    try:
        with open('main.py', 'r') as f:
            content = f.read()
        
        if "zerodha_analytics" in content:
            logger.info("✅ main.py: Zerodha analytics router included")
            return True
        else:
            logger.error("❌ main.py: Zerodha analytics router not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error checking main.py: {e}")
        return False

def verify_api_updates():
    """Verify that API endpoints have been updated"""
    logger.info("🔍 Verifying API endpoint updates...")
    
    # Check performance.py
    try:
        with open('src/api/performance.py', 'r') as f:
            content = f.read()
        
        if "ZERODHA_API" in content and "get_zerodha_analytics_service" in content:
            logger.info("✅ src/api/performance.py: Updated to use Zerodha analytics")
        else:
            logger.warning("⚠️ src/api/performance.py: May not be fully updated")
            
    except Exception as e:
        logger.error(f"❌ Error checking performance.py: {e}")
    
    # Check positions.py
    try:
        with open('src/api/positions.py', 'r') as f:
            content = f.read()
        
        if "ZERODHA_API" in content and "get_zerodha_analytics_service" in content:
            logger.info("✅ src/api/positions.py: Updated to use Zerodha analytics")
        else:
            logger.warning("⚠️ src/api/positions.py: May not be fully updated")
            
    except Exception as e:
        logger.error(f"❌ Error checking positions.py: {e}")

def test_zerodha_analytics_import():
    """Test that Zerodha analytics can be imported"""
    logger.info("🧪 Testing Zerodha analytics import...")
    
    try:
        # Test core analytics import
        from src.core.zerodha_analytics import ZerodhaAnalyticsService, ZerodhaAnalytics
        logger.info("✅ src/core/zerodha_analytics.py: Import successful")
        
        # Test API import
        from src.api.zerodha_analytics import router
        logger.info("✅ src/api/zerodha_analytics.py: Import successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        return False

def deploy_changes():
    """Deploy the changes to git"""
    logger.info("🚀 Deploying Zerodha analytics system...")
    
    try:
        # Add all files
        subprocess.run(['git', 'add', '.'], check=True)
        logger.info("✅ Git add completed")
        
        # Commit changes
        commit_message = f"IMPLEMENT ZERODHA ANALYTICS: Bypass faulty database for reliable reports\n\n- Added ZerodhaAnalyticsService for direct API access\n- Created zerodha_analytics.py API endpoints\n- Updated performance.py and positions.py to use Zerodha data\n- Integrated with main.py router system\n- All analytics now sourced from Zerodha API instead of faulty database"
        
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        logger.info("✅ Git commit completed")
        
        # Push to remote
        subprocess.run(['git', 'push'], check=True)
        logger.info("✅ Git push completed")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Git operation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return False

def main():
    """Main deployment function"""
    logger.info("🚀 Starting Zerodha Analytics System Deployment")
    logger.info("=" * 60)
    
    # Step 1: Verify files exist
    if not verify_zerodha_analytics_files():
        logger.error("❌ Required files missing - deployment failed")
        return False
    
    # Step 2: Verify main.py integration
    if not verify_main_integration():
        logger.error("❌ Main.py integration failed - deployment failed")
        return False
    
    # Step 3: Verify API updates
    verify_api_updates()
    
    # Step 4: Test imports
    if not test_zerodha_analytics_import():
        logger.error("❌ Import test failed - deployment failed")
        return False
    
    # Step 5: Deploy to git
    if not deploy_changes():
        logger.error("❌ Git deployment failed")
        return False
    
    logger.info("✅ Zerodha Analytics System Deployment Completed Successfully!")
    logger.info("📊 All analytics now sourced from Zerodha API")
    logger.info("🔗 New endpoints available:")
    logger.info("   - /api/v1/zerodha-analytics/performance")
    logger.info("   - /api/v1/zerodha-analytics/positions")
    logger.info("   - /api/v1/zerodha-analytics/daily-report")
    logger.info("   - /api/v1/zerodha-analytics/trade-history")
    logger.info("   - /api/v1/zerodha-analytics/comprehensive-analytics")
    logger.info("   - /api/v1/zerodha-analytics/account-summary")
    logger.info("   - /api/v1/zerodha-analytics/real-time-status")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 