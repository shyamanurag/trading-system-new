#!/usr/bin/env python3
"""
Fix Redis Recursion Error in Production
Deploys the fix for the "encoding with 'idna' codec failed (RecursionError: maximum recursion depth exceeded in comparison)" error
"""

import os
import sys
import logging
import subprocess
import time

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def deploy_redis_fix():
    """Deploy the Redis recursion error fix to production"""
    
    logger.info("🚀 Deploying Redis recursion error fix...")
    
    try:
        # Check if we're in the right directory
        if not os.path.exists('data/truedata_client.py'):
            logger.error("❌ Not in project root directory")
            return False
        
        # Verify the fix is in place
        with open('data/truedata_client.py', 'r') as f:
            content = f.read()
            if 'create_safe_market_data' not in content:
                logger.error("❌ Redis fix not found in truedata_client.py")
                return False
        
        logger.info("✅ Redis fix verified in code")
        
        # Deploy to DigitalOcean App Platform
        logger.info("📦 Deploying to DigitalOcean App Platform...")
        
        # Use git push to trigger deployment
        try:
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True)
            logger.info("✅ Git add completed")
            
            # Commit changes
            commit_message = "fix: resolve Redis recursion error in market data storage"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            logger.info("✅ Git commit completed")
            
            # Push to trigger deployment
            subprocess.run(['git', 'push'], check=True)
            logger.info("✅ Git push completed - deployment triggered")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Git operation failed: {e}")
            return False
        
        logger.info("⏳ Waiting for deployment to complete...")
        logger.info("💡 Monitor deployment at: https://cloud.digitalocean.com/apps")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return False

def verify_fix():
    """Verify the Redis fix is working"""
    logger.info("🔍 Verifying Redis fix...")
    
    try:
        # Test the safe serialization function
        from data.truedata_client import create_safe_market_data, safe_json_serialize
        
        # Test data
        test_data = {
            'symbol': 'RELIANCE',
            'ltp': 1387.80,
            'high': 1390.50,
            'low': 1385.20,
            'open': 1388.90,
            'volume': 427588,
            'change': -3.90,
            'change_percent': -0.28,
            'timestamp': '2025-07-28T03:48:57',
            'data_quality': {
                'has_ohlc': True,
                'has_volume': True,
                'has_change_percent': True
            }
        }
        
        # Test safe serialization
        safe_data = create_safe_market_data(test_data)
        import json
        json_str = json.dumps(safe_data)
        
        logger.info("✅ Safe serialization test passed")
        logger.info(f"📊 Test data serialized: {len(json_str)} characters")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fix verification failed: {e}")
        return False

def main():
    """Main deployment function"""
    logger.info("🔧 Redis Recursion Error Fix Deployment")
    logger.info("=" * 50)
    
    # Verify the fix
    if not verify_fix():
        logger.error("❌ Fix verification failed - aborting deployment")
        return False
    
    # Deploy the fix
    if not deploy_redis_fix():
        logger.error("❌ Deployment failed")
        return False
    
    logger.info("✅ Redis recursion error fix deployed successfully")
    logger.info("📊 Monitor logs for: 'Redis storage error' messages")
    logger.info("💡 Expected: No more recursion errors in market data storage")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 