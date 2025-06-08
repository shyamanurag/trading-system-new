#!/usr/bin/env python3
"""
Windows Connection Optimization Script
Fixes semaphore timeout and connection issues on Windows environments
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from data.database_manager import DatabaseManager
from utils.redis_manager import RedisManager
from core.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WindowsConnectionOptimizer:
    def __init__(self):
        self.config_manager = ConfigManager()
        
    async def optimize_database_connections(self):
        """Optimize PostgreSQL connections for Windows"""
        try:
            logger.info("🔧 Optimizing PostgreSQL connections for Windows...")
            
            # Set Windows-specific environment variables
            os.environ['PGCONNECT_TIMEOUT'] = '60'
            os.environ['PGSSLMODE'] = 'require'
            os.environ['PGCLIENTENCODING'] = 'UTF8'
            
            # Configure connection pooling for Windows
            pool_config = {
                'pool_size': 3,
                'max_overflow': 5,
                'pool_timeout': 60,
                'pool_recycle': 1800,
                'pool_pre_ping': True,
                'echo': False,
                'connect_args': {
                    'connect_timeout': 60,
                    'command_timeout': 60,
                    'server_settings': {
                        'application_name': 'trading_system_windows',
                        'tcp_keepalives_idle': '600',
                        'tcp_keepalives_interval': '30',
                        'tcp_keepalives_count': '3'
                    }
                }
            }
            
            # Test database connection with optimized settings
            db_manager = DatabaseManager()
            await db_manager.initialize_with_config(pool_config)
            
            # Test connection
            async with db_manager.get_connection() as conn:
                result = await conn.execute("SELECT 1 as test")
                await result.fetchone()
                
            logger.info("✅ PostgreSQL connection optimization successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL optimization failed: {str(e)}")
            return False
            
    async def optimize_redis_connections(self):
        """Optimize Redis connections for Windows"""
        try:
            logger.info("🔧 Optimizing Redis connections for Windows...")
            
            # Windows-specific Redis configuration
            redis_config = {
                'socket_timeout': 10,
                'socket_connect_timeout': 10,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
                'connection_pool_kwargs': {
                    'max_connections': 10,
                    'retry_on_timeout': True,
                    'health_check_interval': 30
                },
                'retry_on_error': [ConnectionError, TimeoutError],
                'retry': 3,
                'retry_delay': 1
            }
            
            # Test Redis connection with optimized settings
            redis_manager = RedisManager()
            await redis_manager.initialize_with_config(redis_config)
            
            # Test Redis operations
            await redis_manager.set("windows_test", "connection_ok", ex=10)
            result = await redis_manager.get("windows_test")
            
            if result == "connection_ok":
                logger.info("✅ Redis connection optimization successful")
                await redis_manager.delete("windows_test")
                return True
            else:
                raise Exception("Redis test failed")
                
        except Exception as e:
            logger.error(f"❌ Redis optimization failed: {str(e)}")
            return False
            
    async def set_windows_event_loop_policy(self):
        """Set optimal event loop policy for Windows"""
        try:
            if sys.platform.startswith('win'):
                logger.info("🔧 Setting Windows ProactorEventLoopPolicy...")
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                logger.info("✅ Windows event loop policy set successfully")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to set Windows event loop policy: {str(e)}")
            return False
            
    async def optimize_system_limits(self):
        """Optimize system limits for Windows"""
        try:
            logger.info("🔧 Optimizing system limits for Windows...")
            
            # Set environment variables for connection limits
            os.environ['PYTHONHTTPSVERIFY'] = '1'
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            
            # Optimize asyncio settings
            if hasattr(asyncio, 'set_event_loop_policy'):
                policy = asyncio.WindowsProactorEventLoopPolicy()
                asyncio.set_event_loop_policy(policy)
                
            logger.info("✅ System limits optimization successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ System limits optimization failed: {str(e)}")
            return False
            
    async def run_optimization(self):
        """Run complete Windows optimization"""
        logger.info("🚀 Starting Windows Connection Optimization...")
        
        results = []
        
        # Set event loop policy first
        results.append(await self.set_windows_event_loop_policy())
        
        # Optimize system limits
        results.append(await self.optimize_system_limits())
        
        # Optimize database connections
        results.append(await self.optimize_database_connections())
        
        # Optimize Redis connections  
        results.append(await self.optimize_redis_connections())
        
        success_count = sum(results)
        total_count = len(results)
        
        if success_count == total_count:
            logger.info("🎉 All Windows optimizations completed successfully!")
            return True
        else:
            logger.warning(f"⚠️ {success_count}/{total_count} optimizations successful")
            return False

async def main():
    """Main optimization function"""
    optimizer = WindowsConnectionOptimizer()
    success = await optimizer.run_optimization()
    
    if success:
        print("\n✅ Windows optimization completed successfully!")
        print("You can now start the trading system with improved performance.")
    else:
        print("\n❌ Some optimizations failed. Check logs for details.")
        
    return success

if __name__ == "__main__":
    try:
        # Set Windows event loop policy if needed
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Optimization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Optimization failed: {str(e)}")
        sys.exit(1) 