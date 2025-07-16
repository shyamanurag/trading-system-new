"""
Dynamic User Manager for Paper Trading
Automatically creates and manages paper trading users
Works with both development and production database schemas
"""

import logging
from typing import Optional, Union
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

logger = logging.getLogger(__name__)

class PaperTradingUserManager:
    """Manages paper trading users dynamically"""
    
    @staticmethod
    def ensure_user_exists(db_session: Session, user_id: Optional[int] = None) -> Union[int, str]:
        """
        Ensure a paper trading user exists and return the user identifier
        Returns id (primary key) for production database
        """
        try:
            # Check if this is production database (PostgreSQL) or development (SQLite)
            result = db_session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'id'
            """))
            
            has_id_column = result.fetchone() is not None
            logger.info(f"📊 Database schema detected - has 'id' column: {has_id_column}")
        except:
            # For SQLite or if information_schema doesn't exist, assume id column exists
            has_id_column = True
            logger.info("📊 Assuming SQLite database with 'id' column")
                
        try:        
            if has_id_column:
                # Standard database with id column (both production and development)
                logger.info("📊 Using standard database schema with 'id' primary key")
                
                if user_id:
                    # Check if specific user exists
                    result = db_session.execute(text("""
                        SELECT id FROM users WHERE id = :user_id
                    """), {"user_id": user_id})
                    
                    if result.fetchone():
                        return user_id
                        
                # Check if any paper trading user exists
                result = db_session.execute(text("""
                    SELECT id FROM users 
                    WHERE username = 'PAPER_TRADER_001' 
                    OR trading_enabled = true 
                    LIMIT 1
                """))
                
                row = result.fetchone()
                if row:
                    logger.info(f"✅ Found existing paper trading user with id: {row[0]}")
                    return row[0]
                    
                # Create paper user - let SERIAL auto-generate id
                logger.info("📝 Creating paper trading user...")
                
                # Don't include id in INSERT - let SERIAL generate it
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
                        :true_val, 'PAPER', :true_val,
                        1000, 500000, :now, :now
                    ) ON CONFLICT (username) DO NOTHING
                """), {
                    'true_val': True,
                    'now': datetime.now()
                })
                db_session.commit()
                
                # Get the created user id
                result = db_session.execute(text("""
                    SELECT id FROM users WHERE username = 'PAPER_TRADER_001'
                """))
                row = result.fetchone()
                if row:
                    logger.info(f"✅ Paper trading user ready with id: {row[0]}")
                    return row[0]
                else:
                    logger.warning("⚠️ Paper trading user creation may have failed, using fallback")
                    return 1
                    
            else:
                # Fallback for unusual database schemas
                logger.info("📝 Using fallback approach for unusual database schema")
                
                # Try to create with minimal fields
                db_session.execute(text("""
                    INSERT INTO users (username, email, password_hash, trading_enabled) 
                    VALUES ('PAPER_TRADER_001', 'paper@algoauto.com', 'dummy_hash', true)
                    ON CONFLICT (username) DO NOTHING
                """))
                db_session.commit()
                
                return 'PAPER_TRADER_001'  # Return username as identifier
                    
        except Exception as e:
            logger.error(f"❌ Error ensuring user exists: {e}")
            # Return a safe fallback
            return 1
    
    @staticmethod
    def get_paper_trading_user_id(db_session: Session) -> Union[int, str]:
        """Get paper trading user identifier quickly"""
        try:
            # Try to get existing paper user
            result = db_session.execute(text("""
                SELECT id FROM users WHERE username = 'PAPER_TRADER_001' LIMIT 1
            """))
            row = result.fetchone()
            if row:
                return row[0]
                
            # If no paper user exists, create one
            return PaperTradingUserManager.ensure_user_exists(db_session)
        except:
            # If id column doesn't exist, try username approach
            try:
                result = db_session.execute(text("""
                    SELECT username FROM users WHERE username = 'PAPER_TRADER_001' LIMIT 1
                """))
                row = result.fetchone()
                if row:
                    return row[0]
                return 'PAPER_TRADER_001'
            except:
                return 1
                
    @staticmethod
    def validate_user_exists(db_session: Session, user_identifier: Union[int, str]) -> bool:
        """Validate that a user exists in the database"""
        try:
            if isinstance(user_identifier, int):
                # Check by id
                result = db_session.execute(text("""
                    SELECT 1 FROM users WHERE id = :user_id LIMIT 1
                """), {"user_id": user_identifier})
            else:
                # Check by username
                result = db_session.execute(text("""
                    SELECT 1 FROM users WHERE username = :username LIMIT 1
                """), {"username": user_identifier})
                
            return result.fetchone() is not None
        except Exception as e:
            logger.error(f"❌ Error validating user exists: {e}")
            return False

    @staticmethod  
    def create_demo_user_if_needed(db_session: Session) -> Union[int, str]:
        """Create a demo user for testing purposes"""
        try:
            # Check if demo user already exists
            result = db_session.execute(text("""
                SELECT id FROM users WHERE username = 'demo_user' LIMIT 1
            """))
            
            row = result.fetchone()
            if row:
                return row[0]
                
            # Create demo user
            db_session.execute(text("""
                INSERT INTO users (
                    username, email, password_hash, full_name,
                    trading_enabled, is_active
                ) VALUES (
                    'demo_user', 'demo@algoauto.com', 'demo_hash', 'Demo User',
                    true, true
                ) ON CONFLICT (username) DO NOTHING
            """))
            db_session.commit()
            
            # Get created user id
            result = db_session.execute(text("""
                SELECT id FROM users WHERE username = 'demo_user'
            """))
            row = result.fetchone()
            if row:
                return row[0]
            return 1
            
        except Exception as e:
            logger.error(f"❌ Error creating demo user: {e}")
            return 1 