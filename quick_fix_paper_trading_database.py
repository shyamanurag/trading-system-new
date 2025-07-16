#!/usr/bin/env python3
"""
Quick Fix for Paper Trading Database User Creation
Resolves the 'user_id' constraint violations
"""

import logging
import sys
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_paper_trading_user():
    """Fix paper trading user creation in database"""
    try:
        from src.core.database import get_db
        from sqlalchemy import text
        
        logger.info("🔧 PAPER TRADING DATABASE FIX")
        logger.info("=" * 50)
        
        # Get database session
        db_session = next(get_db())
        
        # Check current database schema
        logger.info("📊 Checking database schema...")
        
        try:
            # Check if users table exists and get its structure
            result = db_session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            logger.info(f"📋 Users table has {len(columns)} columns:")
            for col in columns:
                logger.info(f"   - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
                
        except Exception as e:
            logger.error(f"❌ Error checking schema: {e}")
            
        # Check if paper trading user already exists
        logger.info("\n📋 Checking existing users...")
        try:
            result = db_session.execute(text("""
                SELECT id, username, email, trading_enabled, is_active 
                FROM users 
                ORDER BY id
            """))
            
            users = result.fetchall()
            logger.info(f"👥 Found {len(users)} existing users:")
            for user in users:
                logger.info(f"   - ID: {user[0]}, Username: {user[1]}, Trading: {user[3]}, Active: {user[4]}")
                
            # Check specifically for paper trading user
            result = db_session.execute(text("""
                SELECT id FROM users WHERE username = 'PAPER_TRADER_001'
            """))
            paper_user = result.fetchone()
            
            if paper_user:
                logger.info(f"✅ Paper trading user exists with ID: {paper_user[0]}")
                return paper_user[0]
                
        except Exception as e:
            logger.error(f"❌ Error checking existing users: {e}")
            
        # Create paper trading user
        logger.info("\n📝 Creating paper trading user...")
        try:
            # Insert without specifying id - let SERIAL auto-generate
            db_session.execute(text("""
                INSERT INTO users (
                    username, email, password_hash, full_name,
                    initial_capital, current_balance, risk_tolerance,
                    is_active, zerodha_client_id, trading_enabled,
                    max_daily_trades, max_position_size, created_at, updated_at
                ) VALUES (
                    'PAPER_TRADER_001', 'paper@algoauto.com',
                    '$2b$12$dummy.hash.paper.trading', 'Paper Trading Account',
                    100000, 100000, 'medium',
                    true, 'PAPER', true,
                    1000, 500000, :now, :now
                ) ON CONFLICT (username) DO NOTHING
            """), {'now': datetime.now()})
            
            db_session.commit()
            logger.info("✅ Paper trading user creation SQL executed")
            
            # Verify user was created
            result = db_session.execute(text("""
                SELECT id, username FROM users WHERE username = 'PAPER_TRADER_001'
            """))
            paper_user = result.fetchone()
            
            if paper_user:
                logger.info(f"🎉 SUCCESS: Paper trading user created with ID: {paper_user[0]}")
                return paper_user[0]
            else:
                logger.error("❌ Paper trading user not found after creation")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating paper trading user: {e}")
            try:
                db_session.rollback()
            except:
                pass
            return None
            
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return None
    finally:
        try:
            if 'db_session' in locals():
                db_session.close()
        except:
            pass

def test_trade_creation():
    """Test creating a sample trade"""
    try:
        from src.core.database import get_db
        from sqlalchemy import text
        
        logger.info("\n🧪 Testing trade creation...")
        
        db_session = next(get_db())
        
        # Get paper trading user ID
        result = db_session.execute(text("""
            SELECT id FROM users WHERE username = 'PAPER_TRADER_001'
        """))
        user = result.fetchone()
        
        if not user:
            logger.error("❌ No paper trading user found")
            return False
            
        user_id = user[0]
        logger.info(f"📋 Using user ID: {user_id}")
        
        # Create test trade
        test_order_id = f"TEST_{int(time.time())}"
        
        db_session.execute(text("""
            INSERT INTO trades (
                order_id, user_id, symbol, trade_type, quantity,
                price, commission, strategy, executed_at, created_at
            ) VALUES (
                :order_id, :user_id, 'TEST_SYMBOL', 'BUY', 10,
                100.0, 0, 'test_strategy', NOW(), NOW()
            )
        """), {
            'order_id': test_order_id,
            'user_id': user_id
        })
        
        db_session.commit()
        logger.info(f"✅ Test trade created successfully: {test_order_id}")
        
        # Verify trade exists
        result = db_session.execute(text("""
            SELECT trade_id, symbol, trade_type, quantity, price 
            FROM trades WHERE order_id = :order_id
        """), {'order_id': test_order_id})
        
        trade = result.fetchone()
        if trade:
            logger.info(f"🎉 Trade verified: ID {trade[0]}, {trade[1]} {trade[2]} {trade[3]} @ {trade[4]}")
            return True
        else:
            logger.error("❌ Trade not found after creation")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing trade creation: {e}")
        return False
    finally:
        try:
            if 'db_session' in locals():
                db_session.close()
        except:
            pass

if __name__ == "__main__":
    logger.info("🚀 Starting Paper Trading Database Fix")
    
    # Fix user creation
    user_id = fix_paper_trading_user()
    
    if user_id:
        # Test trade creation
        success = test_trade_creation()
        if success:
            logger.info("\n🎉 PAPER TRADING DATABASE FIX: SUCCESS")
            logger.info("✅ Paper trading user exists")
            logger.info("✅ Trade creation working")
            logger.info("✅ Database schema compatible")
        else:
            logger.error("\n❌ PAPER TRADING DATABASE FIX: PARTIAL")
            logger.error("✅ Paper trading user exists")
            logger.error("❌ Trade creation failed")
    else:
        logger.error("\n❌ PAPER TRADING DATABASE FIX: FAILED")
        logger.error("❌ Could not create paper trading user")
        
    logger.info("\n📋 Next steps:")
    logger.info("1. Run this script to fix database")
    logger.info("2. Restart trading system") 
    logger.info("3. Monitor trade execution logs") 