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
        Updated to handle actual production database schema
        """
        try:
            # First, determine the actual database schema
            try:
                # Check what columns exist and their types
                result = db_session.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name IN ('id', 'user_id')
                """))
                
                columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in result.fetchall()}
                logger.info(f"📊 Database schema detected: {columns}")
                
                has_id = 'id' in columns
                has_user_id = 'user_id' in columns
                user_id_type = columns.get('user_id', {}).get('type', '')
                
            except Exception as e:
                logger.warning(f"Could not detect schema: {e}, using fallback")
                has_id = True
                has_user_id = False
                user_id_type = 'integer'
                
            # Try to find existing paper trading user
            if has_user_id:
                # Production database has user_id column
                result = db_session.execute(text("""
                    SELECT user_id FROM users WHERE username = 'PAPER_TRADER_001' LIMIT 1
                """))
                row = result.fetchone()
                if row:
                    logger.info(f"✅ Found existing paper trading user with user_id: {row[0]}")
                    return row[0]
                    
                # Create paper trading user for production database
                logger.info("📝 Creating paper trading user for production database...")
                
                if 'character' in user_id_type.lower() or 'varchar' in user_id_type.lower():
                    # user_id is character varying - use string
                    db_session.execute(text("""
                        INSERT INTO users (user_id, username, email, password_hash) 
                        VALUES ('PAPER_001', 'PAPER_TRADER_001', 'paper@algoauto.com', 'dummy_hash')
                        ON CONFLICT (username) DO NOTHING
                    """))
                    db_session.commit()
                    return 'PAPER_001'
                else:
                    # user_id is integer - use integer
                    db_session.execute(text("""
                        INSERT INTO users (user_id, username, email, password_hash) 
                        VALUES (1001, 'PAPER_TRADER_001', 'paper@algoauto.com', 'dummy_hash')
                        ON CONFLICT (username) DO NOTHING
                    """))
                    db_session.commit()
                    return 1001
                    
            elif has_id:
                # Development database with id column (auto-generated)
                result = db_session.execute(text("""
                    SELECT id FROM users WHERE username = 'PAPER_TRADER_001' LIMIT 1
                """))
                row = result.fetchone()
                if row:
                    logger.info(f"✅ Found existing paper trading user with id: {row[0]}")
                    return row[0]
                    
                # Create paper trading user - let SERIAL auto-generate id
                logger.info("📝 Creating paper trading user for development database...")
                db_session.execute(text("""
                    INSERT INTO users (username, email, password_hash, trading_enabled) 
                    VALUES ('PAPER_TRADER_001', 'paper@algoauto.com', 'dummy_hash', true)
                    ON CONFLICT (username) DO NOTHING
                """))
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
                logger.warning("📝 Using fallback approach - no standard id columns found")
                return 'PAPER_TRADER_001'
                    
        except Exception as e:
            logger.error(f"❌ Error ensuring user exists: {e}")
            # Return a safe fallback based on what we expect
            return 'PAPER_001'  # Use string fallback for production compatibility
    
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