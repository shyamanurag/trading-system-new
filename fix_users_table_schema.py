#!/usr/bin/env python3
"""
Fix Users Table Schema
======================
This script fixes the users table schema issue where the 'id' column is missing.
Based on the migration files, the users table should have an 'id' SERIAL PRIMARY KEY.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def fix_users_table_schema():
    """Fix the users table schema to include the missing id column"""
    
    try:
        from src.core.database import get_db, engine
        from sqlalchemy import text, inspect
        
        print("🔍 Checking users table schema...")
        
        # Get database session
        db_session = next(get_db())
        
        # Check if users table exists and inspect its structure
        inspector = inspect(engine)
        
        if 'users' not in inspector.get_table_names():
            print("❌ Users table does not exist. Running complete schema creation...")
            
            # Run the complete schema from migration 000
            with open('database/migrations/000_reset_database.sql', 'r') as f:
                schema_sql = f.read()
            
            # Execute the schema creation
            db_session.execute(text(schema_sql))
            db_session.commit()
            print("✅ Complete database schema created from migration 000")
            
        else:
            # Check existing columns
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            
            print(f"📋 Current users table columns: {column_names}")
            
            if 'id' not in column_names:
                print("❌ Missing 'id' column in users table. Fixing...")
                
                # Add the missing id column as SERIAL PRIMARY KEY
                fix_sql = """
                -- Add missing id column
                ALTER TABLE users ADD COLUMN id SERIAL PRIMARY KEY;
                """
                
                db_session.execute(text(fix_sql))
                db_session.commit()
                print("✅ Added missing 'id' column to users table")
                
            else:
                print("✅ Users table already has 'id' column")
        
        # Verify the fix worked
        test_query = text("SELECT id FROM users LIMIT 1")
        try:
            result = db_session.execute(test_query)
            print("✅ Successfully verified: 'SELECT id FROM users' query works")
        except Exception as test_error:
            print(f"❌ Test query still fails: {test_error}")
            return False
        
        # Ensure at least one user exists for paper trading
        user_count_query = text("SELECT COUNT(*) FROM users")
        user_count = db_session.execute(user_count_query).scalar()
        
        if user_count == 0:
            print("📝 Creating paper trading user...")
            
            # Insert the paper trading user from migration 004
            insert_user_sql = text("""
                INSERT INTO users (
                    username, 
                    email, 
                    password_hash, 
                    full_name, 
                    initial_capital, 
                    current_balance, 
                    risk_tolerance, 
                    is_active, 
                    zerodha_client_id,
                    trading_enabled,
                    max_daily_trades,
                    max_position_size
                ) VALUES (
                    'PAPER_TRADER_001',
                    'paper.trader@algoauto.com',
                    '$2b$12$dummy.hash.for.paper.trading.user.not.used.for.login',
                    'AlgoAuto Paper Trading Master',
                    100000.00,
                    100000.00,
                    'medium',
                    true,
                    'PAPER_API_KEY',
                    true,
                    1000,
                    500000.00
                )
            """)
            
            db_session.execute(insert_user_sql)
            db_session.commit()
            print("✅ Created paper trading user")
        else:
            print(f"✅ Found {user_count} existing users")
        
        db_session.close()
        print("🎯 Users table schema fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing users table schema: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Starting users table schema fix...")
    
    success = fix_users_table_schema()
    
    if success:
        print("✅ Schema fix completed successfully!")
        print("📋 Paper trading should now work correctly.")
        sys.exit(0)
    else:
        print("❌ Schema fix failed!")
        sys.exit(1) 