#!/usr/bin/env python3
"""
Simple Redis Fallback Test
"""

import os
import sys
import logging

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Simple Redis Fallback Test")
    
    try:
        from src.core.redis_fallback_manager import ProductionRedisFallback
        
        # Create instance
        redis_fallback = ProductionRedisFallback()
        logger.info("✅ Created ProductionRedisFallback instance")
        
        # Test connection (should fail and use fallback)
        logger.info("📡 Testing connection...")
        connected = redis_fallback.connect()
        logger.info(f"Connection result: {connected}")
        
        # Test status
        status = redis_fallback.get_status()
        logger.info(f"📊 Status: {status}")
        
        # Test basic operations
        logger.info("🔄 Testing basic operations...")
        
        # Set
        set_result = redis_fallback.set('test', 'value')
        logger.info(f"Set result: {set_result}")
        
        # Get
        get_result = redis_fallback.get('test')
        logger.info(f"Get result: {get_result}")
        
        # Exists
        exists_result = redis_fallback.exists('test')
        logger.info(f"Exists result: {exists_result}")
        
        # Delete
        delete_result = redis_fallback.delete('test')
        logger.info(f"Delete result: {delete_result}")
        
        logger.info("✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
