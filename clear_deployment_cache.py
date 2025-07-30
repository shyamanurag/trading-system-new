#!/usr/bin/env python3
"""
Clear Signal Processing Cache
============================
Clears ONLY the signal processing cache from Redis after deployment to prevent
processing old cached signals, while preserving order tracking and position data
that's needed for square-off trades and real position tracking.
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
import redis.asyncio as redis

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SignalCacheCleaner:
    """Clears ONLY signal processing cache while preserving order/position tracking"""
    
    def __init__(self):
        self.redis_client = None
        
    async def connect_redis(self):
        """Connect to Redis"""
        try:
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                logger.error("❌ No REDIS_URL environment variable found")
                return False
                
            self.redis_client = redis.from_url(
                redis_url, 
                decode_responses=True,
                ssl_cert_reqs=None,
                ssl_check_hostname=False
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
            logger.info(f"🔗 Connected to: {redis_url[:30]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            return False
    
    async def clear_signal_execution_cache_only(self):
        """Clear ONLY the signal execution deduplication cache - preserve order tracking"""
        try:
            # Clear executed signals deduplication cache for today only
            today = datetime.now().strftime('%Y-%m-%d')
            pattern = f"executed_signals:{today}:*"
            
            logger.info(f"🧹 Clearing signal execution cache for {today}...")
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"✅ Cleared {deleted} signal execution cache entries")
                
                # Log what was cleared for transparency
                for key in keys[:5]:  # Show first 5 as examples
                    logger.info(f"   Cleared: {key}")
                if len(keys) > 5:
                    logger.info(f"   ... and {len(keys) - 5} more signal cache entries")
            else:
                logger.info("ℹ️ No signal execution cache found to clear")
            
            return len(keys) if keys else 0
            
        except Exception as e:
            logger.error(f"❌ Error clearing signal execution cache: {e}")
            return 0
    
    async def clear_strategy_signal_cache(self):
        """Clear strategy-generated signal cache (not order tracking)"""
        try:
            patterns_to_clear = [
                "strategy_signals:*",
                "pending_signals:*", 
                "signal_queue:*",
                "cached_signals:*"
            ]
            
            total_cleared = 0
            for pattern in patterns_to_clear:
                logger.info(f"🧹 Clearing strategy cache pattern: {pattern}")
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    total_cleared += deleted
                    logger.info(f"   Cleared {deleted} strategy signal cache entries")
                else:
                    logger.info(f"   No strategy cache found for pattern {pattern}")
            
            return total_cleared
            
        except Exception as e:
            logger.error(f"❌ Error clearing strategy signal cache: {e}")
            return 0
    
    async def preserve_important_cache(self):
        """Show what cache we're preserving (for transparency)"""
        try:
            preserved_patterns = [
                "orders:*",          # Order tracking - KEEP
                "positions:*",       # Position tracking - KEEP  
                "trades:*",          # Trade history - KEEP
                "balances:*",        # Balance tracking - KEEP
                "portfolio:*",       # Portfolio data - KEEP
                "market_data:*",     # Market data - KEEP for faster startup
                "instruments:*",     # Instrument data - KEEP
                "user_session:*",    # User sessions - KEEP
                "zerodha_auth:*"     # Authentication - KEEP
            ]
            
            total_preserved = 0
            logger.info("🔒 PRESERVING IMPORTANT CACHE (for order tracking & positions):")
            
            for pattern in preserved_patterns:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    total_preserved += len(keys)
                    logger.info(f"   Preserving {len(keys)} entries: {pattern}")
                else:
                    logger.info(f"   No entries found: {pattern}")
            
            logger.info(f"🔒 Total cache entries preserved: {total_preserved}")
            return total_preserved
            
        except Exception as e:
            logger.error(f"❌ Error checking preserved cache: {e}")
            return 0
    
    async def get_cache_statistics(self):
        """Get cache statistics"""
        try:
            info = await self.redis_client.info()
            total_keys = await self.redis_client.dbsize()
            
            logger.info("📊 REDIS CACHE STATISTICS:")
            logger.info(f"   Total keys: {total_keys}")
            logger.info(f"   Used memory: {info.get('used_memory_human', 'N/A')}")
            logger.info(f"   Connected clients: {info.get('connected_clients', 'N/A')}")
            
            return {
                'total_keys': total_keys,
                'used_memory': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting cache statistics: {e}")
            return {}
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("🔌 Redis connection closed")

async def main():
    """Main function to clear signal processing cache only"""
    logger.info("🚀 Starting SELECTIVE Cache Clearing")
    logger.info("This will clear ONLY signal processing cache while preserving order/position tracking")
    logger.info("=" * 80)
    
    cleaner = SignalCacheCleaner()
    
    try:
        # Connect to Redis
        if not await cleaner.connect_redis():
            logger.error("❌ Cannot connect to Redis - cache clearing failed")
            return
        
        # Get initial statistics
        logger.info("📊 BEFORE CLEARING:")
        initial_stats = await cleaner.get_cache_statistics()
        
        # Show what we're preserving
        preserved_count = await cleaner.preserve_important_cache()
        
        # Clear only signal processing cache
        logger.info("\n🧹 STARTING SELECTIVE CACHE CLEARING...")
        logger.info("🎯 Target: Signal processing cache ONLY")
        logger.info("🔒 Preserve: Order tracking, positions, trades, balances")
        
        signal_execution_cleared = await cleaner.clear_signal_execution_cache_only()
        strategy_signals_cleared = await cleaner.clear_strategy_signal_cache()
        
        # Get final statistics
        logger.info("\n📊 AFTER CLEARING:")
        final_stats = await cleaner.get_cache_statistics()
        
        # Summary
        total_cleared = signal_execution_cleared + strategy_signals_cleared
        
        logger.info("=" * 80)
        logger.info("📋 SELECTIVE CACHE CLEARING SUMMARY:")
        logger.info(f"   🧹 Signal execution cache cleared: {signal_execution_cleared}")
        logger.info(f"   🧹 Strategy signal cache cleared: {strategy_signals_cleared}")
        logger.info(f"   🧹 Total signal cache cleared: {total_cleared}")
        logger.info(f"   🔒 Important cache preserved: {preserved_count}")
        
        if initial_stats.get('total_keys') and final_stats.get('total_keys'):
            keys_reduction = initial_stats['total_keys'] - final_stats['total_keys']
            logger.info(f"   📉 Keys reduced: {keys_reduction}")
            logger.info(f"   📊 Keys remaining: {final_stats['total_keys']}")
        
        logger.info("=" * 80)
        
        if total_cleared > 0:
            logger.info("✅ SELECTIVE CACHE CLEARING COMPLETED!")
            logger.info("✅ Signal processing cache cleared - no duplicate signals after deployment")
            logger.info("🔒 Order tracking & position data preserved - square-off trades will work")
        else:
            logger.info("ℹ️ No signal cache found to clear - system already clean")
            
        logger.info("\n🎯 RESULT: Clean slate for signal processing, preserved order tracking")
            
    except Exception as e:
        logger.error(f"❌ Cache clearing failed: {e}")
    finally:
        await cleaner.close()

if __name__ == "__main__":
    asyncio.run(main()) 