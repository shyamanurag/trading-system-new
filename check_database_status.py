#!/usr/bin/env python3
"""
Database Status Checker
=======================
Check if migration 009 was applied and users table is properly configured.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def check_database_status():
    """Check the current database state"""
    
    try:
        from src.core.database import get_db
        from sqlalchemy import text
        
        print("🔍 Checking database status...")
        print("=" * 50)
        
        # Get database session
        db_session = next(get_db())
        if not db_session:
            print("❌ Database connection failed")
            return False
        
        # Check if users table exists and has id column
        try:
            result = db_session.execute(text("SELECT id, username, email, is_active, trading_enabled FROM users"))
            users = result.fetchall()
            
            print("✅ Users table exists and id column is present!")
            print(f"📊 Found {len(users)} users:")
            
            for user in users:
                user_id, username, email, is_active, trading_enabled = user
                status = "✅ ACTIVE" if is_active else "❌ INACTIVE"
                trading_status = "✅ ENABLED" if trading_enabled else "❌ DISABLED"
                print(f"  - ID: {user_id}, Username: {username}")
                print(f"    Email: {email}")
                print(f"    Status: {status}, Trading: {trading_status}")
                print()
                
        except Exception as e:
            print(f"❌ Error querying users table: {e}")
            return False
        
        # Check orders table
        try:
            order_count = db_session.execute(text("SELECT COUNT(*) FROM orders")).scalar()
            print(f"📋 Orders table: {order_count} orders found")
        except Exception as e:
            print(f"⚠️ Orders table issue: {e}")
        
        # Check trades table
        try:
            trade_count = db_session.execute(text("SELECT COUNT(*) FROM trades")).scalar()
            print(f"💰 Trades table: {trade_count} trades found")
        except Exception as e:
            print(f"⚠️ Trades table issue: {e}")
        
        # Check if paper trading user exists and is active
        try:
            paper_user = db_session.execute(
                text("SELECT id, username, is_active, trading_enabled FROM users WHERE username LIKE '%PAPER%' OR email LIKE '%paper%'")
            ).fetchone()
            
            if paper_user:
                user_id, username, is_active, trading_enabled = paper_user
                print(f"🎯 Paper trading user found:")
                print(f"   ID: {user_id}, Username: {username}")
                print(f"   Active: {is_active}, Trading Enabled: {trading_enabled}")
                
                if not is_active:
                    print("⚠️ Paper trading user is INACTIVE - this may prevent trades from saving")
                if not trading_enabled:
                    print("⚠️ Paper trading user has trading DISABLED")
                    
            else:
                print("❌ No paper trading user found - creating one...")
                
                # Create paper trading user
                insert_sql = text("""
                    INSERT INTO users (
                        username, email, password_hash, full_name,
                        initial_capital, current_balance, risk_tolerance,
                        is_active, zerodha_client_id, trading_enabled,
                        max_daily_trades, max_position_size
                    ) VALUES (
                        'PAPER_TRADER_001', 'paper.trader@algoauto.com',
                        '$2b$12$dummy.hash', 'AlgoAuto Paper Trading Master',
                        100000.00, 100000.00, 'medium',
                        true, 'PAPER_API_KEY', true,
                        1000, 500000.00
                    )
                """)
                
                db_session.execute(insert_sql)
                db_session.commit()
                print("✅ Paper trading user created successfully!")
                
        except Exception as e:
            print(f"❌ Error with paper trading user: {e}")
        
        db_session.close()
        
        print("=" * 50)
        print("🎯 Database status check completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database status check failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Database Status Checker")
    print("Verifying migration 009 and paper trading setup")
    print()
    
    success = check_database_status()
    
    if success:
        print("✅ Database check completed successfully!")
    else:
        print("❌ Database check failed!")
        sys.exit(1) 