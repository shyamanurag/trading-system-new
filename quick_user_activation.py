#!/usr/bin/env python3
"""
Quick Direct Database User Activation
Direct SQL approach to activate Master Trader user
"""

import sqlite3
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def activate_master_trader_direct():
    """Direct database activation"""
    try:
        logger.info("🚀 DIRECT: Activating Master Trader user via SQL...")
        
        # Try to find the SQLite database
        db_paths = [
            'trading.db',
            'src/trading.db',
            'data/trading.db',
            'database/trading.db'
        ]
        
        db_path = None
        for path in db_paths:
            if os.path.exists(path):
                db_path = path
                break
                
        if not db_path:
            logger.error("❌ SQLite database not found in expected locations")
            return False
            
        logger.info(f"✅ Found database: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            logger.error("❌ Users table not found")
            return False
            
        # Find Master Trader user
        cursor.execute("""
            SELECT id, username, email, is_active 
            FROM users 
            WHERE username LIKE '%Master%' OR email LIKE '%master%' OR username LIKE '%admin%'
        """)
        
        users = cursor.fetchall()
        
        if not users:
            logger.warning("⚠️ No Master Trader user found - creating one...")
            
            # Create Master Trader user
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, is_active, 
                                 initial_capital, current_balance, zerodha_client_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'Master Trader',
                'master@trading-system.com',
                'hashed_password_placeholder',
                'Master Trader (You)',
                True,
                1000000,
                1000000,
                'MASTER_CLIENT_001',
                datetime.now(),
                datetime.now()
            ))
            
            logger.info("✅ Created Master Trader user")
            
        else:
            logger.info(f"✅ Found {len(users)} potential master users")
            
            # Activate all found users
            for user_id, username, email, is_active in users:
                logger.info(f"🔧 Activating user: {username} ({email})")
                
                cursor.execute("""
                    UPDATE users 
                    SET is_active = 1, updated_at = ?
                    WHERE id = ?
                """, (datetime.now(), user_id))
                
                logger.info(f"✅ Activated user ID {user_id}")
        
        # Commit changes
        conn.commit()
        
        # Verify changes
        cursor.execute("""
            SELECT id, username, email, is_active, initial_capital
            FROM users 
            WHERE username LIKE '%Master%' OR email LIKE '%master%' OR username LIKE '%admin%'
        """)
        
        updated_users = cursor.fetchall()
        
        logger.info("🎯 Final user status:")
        for user_id, username, email, is_active, capital in updated_users:
            status = "ACTIVE" if is_active else "INACTIVE"
            logger.info(f"  {username} ({email}): {status}, Capital: ₹{capital:,}")
            
        conn.close()
        
        logger.info("✅ Database activation completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct activation failed: {e}")
        return False

if __name__ == "__main__":
    success = activate_master_trader_direct()
    if success:
        print("🎉 SUCCESS: Master Trader user activated!")
        print("🚀 Trading system should now process orders!")
    else:
        print("❌ FAILED: User activation unsuccessful") 