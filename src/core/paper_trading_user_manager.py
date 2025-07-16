"""
Dynamic User Manager for Paper Trading
Automatically creates and manages paper trading users
"""

import logging
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class PaperTradingUserManager:
    """Manages paper trading users dynamically"""
    
    @staticmethod
    def ensure_user_exists(db_session: Session, user_id: Optional[int] = None) -> int:
        """
        Ensure a paper trading user exists and return the user_id
        If user_id is provided, creates that specific user
        Otherwise, returns the first available user or creates one
        """
        try:
            # If specific user_id requested, check if it exists
            if user_id:
                result = db_session.execute(
                    text("SELECT id FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                if result.fetchone():
                    return user_id
                    
                # Create the specific user
                db_session.execute(text("""
                    INSERT INTO users (
                        id, username, email, password_hash, full_name,
                        initial_capital, current_balance, risk_tolerance,
                        is_active, zerodha_client_id, trading_enabled,
                        max_daily_trades, max_position_size, created_at, updated_at
                    ) VALUES (
                        :user_id, :username, :email,
                        '$2b$12$dummy.hash.paper.trading', :full_name,
                        100000, 100000, 'medium',
                        true, :client_id, true,
                        1000, 500000, NOW(), NOW()
                    ) ON CONFLICT (id) DO NOTHING
                """), {
                    "user_id": user_id,
                    "username": f"PAPER_USER_{user_id}",
                    "email": f"paper.user.{user_id}@algoauto.com",
                    "full_name": f"Paper Trading User {user_id}",
                    "client_id": f"PAPER_{user_id}"
                })
                db_session.commit()
                logger.info(f"✅ Created paper trading user with id={user_id}")
                return user_id
                
            # No specific user_id, find any existing user
            result = db_session.execute(
                text("SELECT id FROM users WHERE trading_enabled = true LIMIT 1")
            )
            row = result.fetchone()
            if row:
                return row[0]
                
            # No users exist, create the first one
            db_session.execute(text("""
                INSERT INTO users (
                    id, username, email, password_hash, full_name,
                    initial_capital, current_balance, risk_tolerance,
                    is_active, zerodha_client_id, trading_enabled,
                    max_daily_trades, max_position_size, created_at, updated_at
                ) VALUES (
                    1, 'PAPER_USER_1', 'paper.user.1@algoauto.com',
                    '$2b$12$dummy.hash.paper.trading', 'Paper Trading User 1',
                    100000, 100000, 'medium',
                    true, 'PAPER_1', true,
                    1000, 500000, NOW(), NOW()
                ) ON CONFLICT (id) DO NOTHING
            """))
            db_session.commit()
            logger.info("✅ Created first paper trading user")
            return 1
            
        except Exception as e:
            logger.error(f"❌ Error ensuring user exists: {e}")
            # Try rollback and return default
            try:
                db_session.rollback()
            except:
                pass
            return 1  # Default fallback
    
    @staticmethod
    def get_or_create_user_for_session(db_session: Session, session_id: str = None) -> int:
        """
        Get or create a user for a specific trading session
        This allows multiple parallel paper trading sessions
        """
        try:
            # For now, use a single user for all paper trading
            # In future, can create separate users per session
            return PaperTradingUserManager.ensure_user_exists(db_session, user_id=1)
            
        except Exception as e:
            logger.error(f"❌ Error getting user for session: {e}")
            return 1  # Default fallback 