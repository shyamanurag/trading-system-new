#!/usr/bin/env python3
"""
Production Database Fix Deployment Script
Run this script directly on the DigitalOcean production server
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check if we're in the correct environment"""
    logger.info("🔍 Checking environment...")
    
    # Check if we have the required environment variables
    required_vars = ['DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        logger.info("💡 This script should be run on the production server where environment variables are set")
        return False
    
    logger.info("✅ Environment check passed")
    return True

def apply_database_fix():
    """Apply the database schema fix"""
    try:
        logger.info("🔧 Applying database schema fix...")
        
        # Run the database fix script
        result = subprocess.run([
            sys.executable, 'fix_critical_database_production.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Database fix applied successfully!")
            logger.info("Output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
            return True
        else:
            logger.error("❌ Database fix failed!")
            logger.error("Error output:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.error(f"  {line}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to apply database fix: {e}")
        return False

def restart_application():
    """Restart the application to pick up the schema changes"""
    logger.info("🔄 Restarting application...")
    
    # For DigitalOcean App Platform, the app will restart automatically
    # when the database connection is re-established
    logger.info("✅ On DigitalOcean App Platform, the application will restart automatically")
    logger.info("📊 Monitor the application logs to verify the fix")

def main():
    """Main deployment process"""
    logger.info("🚀 PRODUCTION DATABASE FIX DEPLOYMENT")
    logger.info("=" * 50)
    
    # Step 1: Check environment
    if not check_environment():
        logger.error("❌ Environment check failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Apply database fix
    if not apply_database_fix():
        logger.error("❌ Database fix failed. Exiting.")
        sys.exit(1)
    
    # Step 3: Restart application
    restart_application()
    
    logger.info("\n🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
    logger.info("📊 Next steps:")
    logger.info("  1. Monitor application logs for successful startup")
    logger.info("  2. Verify that broker_user_id errors are resolved")
    logger.info("  3. Test trading functionality")

if __name__ == "__main__":
    main() 