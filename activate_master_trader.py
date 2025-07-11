#!/usr/bin/env python3
"""
URGENT: Activate Master Trader User
This script fixes the INACTIVE user status that's blocking all trading operations.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def activate_master_trader():
    """Activate Master Trader user to enable trading"""
    try:
        logger.info("🚀 URGENT: Activating Master Trader user...")
        
        # Try database approach first
        try:
            from database_manager import get_database_operations
            from src.models.trading_models import User
            
            db_ops = await get_database_operations()
            
            # Find Master Trader user
            master_user = None
            try:
                # Try by username
                master_user = await db_ops.get_user_by_username("Master Trader")
                if not master_user:
                    # Try by email
                    master_user = await db_ops.get_user_by_email("master@trading-system.com")
                if not master_user:
                    # Try alternative usernames
                    for username in ["Master Trader (You)", "master", "admin"]:
                        master_user = await db_ops.get_user_by_username(username)
                        if master_user:
                            break
            except Exception as e:
                logger.warning(f"Error finding master user: {e}")
                
            if master_user:
                logger.info(f"✅ Found Master Trader: {master_user.username} ({master_user.email})")
                
                # Activate the user
                update_data = {
                    'is_active': True,
                    'status': 'ACTIVE',
                    'trading_enabled': True,
                    'updated_at': datetime.now()
                }
                
                await db_ops.update_user(master_user.id, update_data)
                logger.info("✅ Master Trader activated in database!")
                
                # Verify the change
                updated_user = await db_ops.get_user(master_user.id)
                logger.info(f"✅ Verification: is_active={updated_user.is_active}, trading_enabled={getattr(updated_user, 'trading_enabled', 'N/A')}")
                
            else:
                logger.error("❌ Master Trader user not found in database")
                
        except Exception as db_error:
            logger.error(f"❌ Database activation failed: {db_error}")
            
        # Try Redis approach as backup
        try:
            logger.info("🔄 Trying Redis activation as backup...")
            
            from src.core.user_manager import UserManager
            from src.core.connection_manager import ConnectionManager
            
            # Initialize connection manager
            conn_manager = ConnectionManager()
            await conn_manager.initialize_all_connections()
            
            # Get Redis connection
            redis_conn = conn_manager.get_redis_connection()
            
            if redis_conn:
                user_manager = UserManager(redis_conn)
                
                # Try to find and activate master user
                users = await user_manager.list_users()
                
                for user in users:
                    if user.username in ["Master Trader", "Master Trader (You)", "master", "admin"]:
                        logger.info(f"🔧 Activating user: {user.username}")
                        
                        # Activate user
                        await user_manager.redis.hset(f'users:{user.id}', 'is_active', 'True')
                        await user_manager.redis.hset(f'users:{user.id}', 'status', 'ACTIVE')
                        await user_manager.redis.hset(f'users:{user.id}', 'trading_enabled', 'True')
                        
                        logger.info("✅ Master Trader activated in Redis!")
                        break
                        
            else:
                logger.warning("⚠️ Redis connection not available")
                
        except Exception as redis_error:
            logger.error(f"❌ Redis activation failed: {redis_error}")
            
        # Try API approach
        try:
            logger.info("🔄 Trying API activation...")
            
            import requests
            
            # Get base URL
            base_url = os.getenv('API_BASE_URL', 'https://algoauto-9gx56.ondigitalocean.app')
            
            # Try to activate via API
            response = requests.put(
                f"{base_url}/api/v1/users/master/activate",
                json={"is_active": True, "trading_enabled": True},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Master Trader activated via API!")
            else:
                logger.warning(f"⚠️ API activation returned: {response.status_code}")
                
        except Exception as api_error:
            logger.error(f"❌ API activation failed: {api_error}")
            
        logger.info("🎯 User activation attempts completed!")
        logger.info("🚀 Now the trading system should be able to process orders!")
        
    except Exception as e:
        logger.error(f"❌ Critical error in activation: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(activate_master_trader()) 