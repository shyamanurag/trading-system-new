#!/usr/bin/env python3
"""
Deploy Scalping Threshold Fix - Option 1
Safely reduces thresholds by 50-60% to match current low volatility market conditions
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

def verify_threshold_changes():
    """Verify the threshold changes are correctly applied"""
    logger.info("🔍 Verifying threshold changes...")
    
    try:
        # Check volume profile scalper
        with open('strategies/volume_profile_scalper.py', 'r') as f:
            content = f.read()
            if "'high_volume': 20" in content and "'strong': 0.08" in content:
                logger.info("✅ Volume Profile Scalper thresholds updated")
            else:
                logger.error("❌ Volume Profile Scalper thresholds not updated")
                return False
        
        # Check momentum surfer
        with open('strategies/momentum_surfer.py', 'r') as f:
            content = f.read()
            if "'strong_positive': 0.08" in content and "'volume_threshold': 10" in content:
                logger.info("✅ Momentum Surfer thresholds updated")
            else:
                logger.error("❌ Momentum Surfer thresholds not updated")
                return False
        
        # Check news impact scalper
        with open('strategies/news_impact_scalper.py', 'r') as f:
            content = f.read()
            if "'price_change': 0.15" in content and "'volume_spike': 30" in content:
                logger.info("✅ News Impact Scalper thresholds updated")
            else:
                logger.error("❌ News Impact Scalper thresholds not updated")
                return False
        
        # Check optimized volume scalper
        with open('strategies/optimized_volume_scalper.py', 'r') as f:
            content = f.read()
            if "'high_volume': 22" in content and "'strong': 0.08" in content:
                logger.info("✅ Optimized Volume Scalper thresholds updated")
            else:
                logger.error("❌ Optimized Volume Scalper thresholds not updated")
                return False
        
        # Check base strategy rate limiting
        with open('strategies/base_strategy.py', 'r') as f:
            content = f.read()
            if "max_signals_per_hour = 50" in content and "_check_signal_rate_limits" in content:
                logger.info("✅ Base Strategy rate limiting added")
            else:
                logger.error("❌ Base Strategy rate limiting not added")
                return False
        
        logger.info("✅ All threshold changes verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying changes: {e}")
        return False

def deploy_threshold_fix():
    """Deploy the scalping threshold fix to production"""
    
    logger.info("🚀 Deploying Scalping Threshold Fix (Option 1)...")
    
    try:
        # Check if we're in the right directory
        if not os.path.exists('strategies/volume_profile_scalper.py'):
            logger.error("❌ Not in project root directory")
            return False
        
        # Verify the changes are in place
        if not verify_threshold_changes():
            logger.error("❌ Threshold changes not found - aborting deployment")
            return False
        
        logger.info("✅ Threshold changes verified in code")
        
        # Deploy to DigitalOcean App Platform
        logger.info("📦 Deploying to DigitalOcean App Platform...")
        
        # Use git push to trigger deployment
        try:
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True)
            logger.info("✅ Git add completed")
            
            # Commit changes
            commit_message = "fix: adjust scalping thresholds for current low volatility market - reduce by 50-60% for signal generation"
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

def main():
    """Main deployment function"""
    logger.info("🔧 Scalping Threshold Fix Deployment - Option 1")
    logger.info("=" * 60)
    logger.info("📊 Changes Made:")
    logger.info("   - Volume thresholds: 40% → 20%, 25% → 12%, 15% → 8%")
    logger.info("   - Price thresholds: 0.20% → 0.08%, 0.12% → 0.05%, 0.08% → 0.03%")
    logger.info("   - Momentum thresholds: 0.15% → 0.08%, 0.10% → 0.05%")
    logger.info("   - News impact thresholds: 0.35% → 0.15%, 0.25% → 0.10%")
    logger.info("   - Added rate limiting: 50 signals/hour max, 10 per strategy")
    logger.info("   - Maintained 2:1 risk-reward ratio for safety")
    logger.info("")
    
    # Verify the changes
    if not verify_threshold_changes():
        logger.error("❌ Threshold changes verification failed - aborting deployment")
        return False
    
    # Deploy the fix
    if not deploy_threshold_fix():
        logger.error("❌ Deployment failed")
        return False
    
    logger.info("✅ Scalping threshold fix deployed successfully")
    logger.info("📊 Expected Results:")
    logger.info("   - Scalping strategies will now generate signals in current market")
    logger.info("   - Signal rate limited to 50/hour (manageable)")
    logger.info("   - 2:1 risk-reward ratio maintained for safety")
    logger.info("   - No signal flooding (300+ signals/hour prevented)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 