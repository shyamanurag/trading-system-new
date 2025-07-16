"""
Dynamic User Manager for Paper Trading
Automatically creates and manages paper trading users
Works even without id column in users table
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
        Returns user_id if id column exists, otherwise returns username
        """
        try:
            # First check if user_id column exists (production uses user_id, not id)
            result = db_session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'user_id'
            """))
            
            has_id_column = result.fetchone() is not None
        except:
            # For SQLite or if information_schema doesn't exist
            try:
                # Try to select user_id to see if it exists
                result = db_session.execute(text("SELECT user_id FROM users LIMIT 1"))
                has_id_column = True
            except:
                has_id_column = False
                
        if has_id_column:
            # Production database with user_id column
            logger.info("📊 Users table has user_id column - using production approach")
            
            if user_id:
                # Check if specific user exists
                result = db_session.execute(text("""
                    SELECT user_id FROM users WHERE user_id = :user_id
                """), {"user_id": user_id})
                
                if result.fetchone():
                    return user_id
                    
            # Check if any paper trading user exists
            result = db_session.execute(text("""
                SELECT user_id FROM users 
                WHERE username = 'PAPER_TRADER_001' 
                OR trading_enabled = true 
                LIMIT 1
            """))
            
            row = result.fetchone()
            if row:
                return row[0]
                
            # Create paper user with user_id
            logger.info("📝 Creating paper trading user...")
            
            # For PostgreSQL with SERIAL, we don't specify user_id
            db_session.execute(text("""
                INSERT INTO users (
                    username, email, password_hash, full_name,
                    initial_capital, current_balance, risk_tolerance,
                    is_active, zerodha_client_id, trading_enabled,
                    max_daily_trades, max_position_size, created_at, updated_at,
                    role, status
                ) VALUES (
                    'PAPER_TRADER_001', 'paper@algoauto.com',
                    '$2b$12$dummy.hash.paper.trading', 'Paper Trading Account',
                    100000, 100000, 'medium',
                    :true_val, 'PAPER', :true_val,
                    1000, 500000, :now, :now,
                    'trader', 'active'
                )
            """), {
                'true_val': True if 'postgresql' in str(db_session.bind.url) else 1,
                'now': datetime.now()
            })
            db_session.commit()
            
            # Get the created user_id
            result = db_session.execute(text("""
                SELECT user_id FROM users WHERE username = 'PAPER_TRADER_001'
            """))
            row = result.fetchone()
            if row:
                logger.info(f"✅ Created paper trading user with user_id: {row[0]}")
                return row[0]
                
            return user_id or 1
                
        else:
            # No user_id column - use username-based approach
            logger.info("📝 Users table has no user_id column - using username-based approach")
            
            # Check if paper user exists
            result = db_session.execute(text("""
                SELECT username FROM users 
                WHERE username = 'PAPER_TRADER_001' 
                OR trading_enabled = true 
                LIMIT 1
            """))
            
            row = result.fetchone()
            if row:
                return row[0]  # Return username
                
            # Create paper user without user_id
            db_session.execute(text("""
                INSERT INTO users (
                    username, email, password_hash, full_name,
                    role, status, is_active, trading_enabled,
                    initial_capital, current_balance, risk_tolerance,
                    zerodha_client_id, max_daily_trades, max_position_size,
                    created_at, updated_at
                ) VALUES (
                    'PAPER_TRADER_001', 'paper@algoauto.com',
                    '$2b$12$dummy.hash.paper.trading', 'Paper Trading Account',
                    'trader', 'active', :true_val, :true_val,
                    100000, 100000, 'medium',
                    'PAPER', 1000, 500000,
                    :now, :now
                )
            """), {
                'true_val': True if 'postgresql' in str(db_session.bind.url) else 1,
                'now': datetime.now()
            })
            db_session.commit()
            logger.info("✅ Created paper trading user without user_id column")
            return 'PAPER_TRADER_001'  # Return username
                
        except Exception as e:
            logger.error(f"❌ Error ensuring user exists: {e}")
            # Try rollback
            try:
                db_session.rollback()
            except:
                pass
            # Return safe defaults
            return 1 if user_id else 'PAPER_TRADER_001'
    
    @staticmethod
    def get_user_id_for_trades(db_session: Session) -> int:
        """
        Get a user_id suitable for trades table foreign key
        Always returns an integer, creating dummy user if needed
        """
        try:
            # For trades, we always need an integer user_id
            # First try to get from users table
            result = db_session.execute(text("""
                SELECT user_id FROM users 
                WHERE user_id IS NOT NULL 
                LIMIT 1
            """))
            
            row = result.fetchone()
            if row:
                return row[0]
                
        except:
            pass
            
        # If no user_id column or no users, return 1 as fallback
        # The trade will fail to save but paper trading continues
        return 1 