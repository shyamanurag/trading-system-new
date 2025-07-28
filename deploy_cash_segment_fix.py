#!/usr/bin/env python3
"""
Deploy Cash Segment Fix - EQUITY SIGNAL THRESHOLD ADJUSTMENT
Fixes the strict 2:1 risk-reward ratio that was rejecting cash segment signals
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

def verify_cash_segment_fix():
    """Verify the cash segment fix is correctly applied"""
    logger.info("🔍 Verifying cash segment fix...")
    
    try:
        # Check base strategy equity signal validation
        with open('strategies/base_strategy.py', 'r') as f:
            content = f.read()
            if "min_risk_reward_ratio = 1.5" in content and "Adjusted for current market conditions" in content:
                logger.info("✅ Base strategy equity signal validation fixed")
            else:
                logger.error("❌ Base strategy equity signal validation not fixed")
                return False
        
        # Check signal deduplicator
        with open('src/core/signal_deduplicator.py', 'r') as f:
            content = f.read()
            if "risk_reward_ratio < 1.5" in content and "ADJUSTED: Minimum 1.5:1" in content:
                logger.info("✅ Signal deduplicator fixed")
            else:
                logger.error("❌ Signal deduplicator not fixed")
                return False
        
        logger.info("✅ All cash segment fixes verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying cash segment fix: {e}")
        return False

def test_cash_segment_signal_generation():
    """Test cash segment signal generation"""
    logger.info("🧪 Testing cash segment signal generation...")
    
    try:
        # Test equity signal generation with 1.5:1 ratio
        test_code = '''
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategies.base_strategy import BaseStrategy

def test_equity_signal():
    config = {'scalping': {'signal_cooldown_seconds': 1}}
    strategy = BaseStrategy(config)
    
    # Test signal with 1.5:1 ratio (should pass now)
    signal = strategy._create_equity_signal(
        symbol='RELIANCE',
        action='BUY',
        entry_price=1387.80,
        stop_loss=1380.00,  # Risk: 7.80
        target=1399.70,     # Reward: 11.90 (1.52:1 ratio)
        confidence=0.75,
        metadata={}
    )
    
    if signal:
        print("✅ Cash segment signal generation test passed")
        return True
    else:
        print("❌ Cash segment signal generation test failed")
        return False

test_equity_signal()
'''
        
        # Write test file
        with open('test_cash_segment.py', 'w') as f:
            f.write(test_code)
        
        # Run test
        result = subprocess.run(['python', 'test_cash_segment.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and "✅ Cash segment signal generation test passed" in result.stdout:
            logger.info("✅ Cash segment signal generation test passed")
            return True
        else:
            logger.error(f"❌ Cash segment signal generation test failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing cash segment signal generation: {e}")
        return False

def deploy_cash_segment_fix():
    """Deploy the cash segment fix"""
    logger.info("🚀 Deploying cash segment fix...")
    
    try:
        # Verify the fix is applied
        if not verify_cash_segment_fix():
            logger.error("❌ Cash segment fix verification failed")
            return False
        
        # Test the signal generation
        if not test_cash_segment_signal_generation():
            logger.error("❌ Cash segment signal generation test failed")
            return False
        
        logger.info("✅ Cash segment fix deployed successfully")
        logger.info("📊 Changes Made:")
        logger.info("   - Equity signal validation: 2.0:1 → 1.5:1 ratio")
        logger.info("   - Signal deduplicator: 2.0:1 → 1.5:1 ratio")
        logger.info("   - Adjusted for current low volatility market")
        logger.info("   - Cash segment signals will now be generated")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error deploying cash segment fix: {e}")
        return False

if __name__ == "__main__":
    success = deploy_cash_segment_fix()
    if success:
        logger.info("🎯 Cash segment fix deployment completed successfully")
    else:
        logger.error("❌ Cash segment fix deployment failed")
        sys.exit(1) 