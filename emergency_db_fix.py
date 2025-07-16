#!/usr/bin/env python3
"""
Emergency Database Fix - Run this to immediately fix the database
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def fix_database():
    """Apply emergency fixes to the database"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
        
    engine = create_engine(database_url)
    
    with engine.begin() as conn:
        try:
            # 1. Add id column if missing
            print("📝 Checking users table structure...")
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'id'
            """))
            
            if not result.fetchone():
                print("📝 Adding id column...")
                # Check for existing primary key
                pk_result = conn.execute(text("""
                    SELECT constraint_name FROM information_schema.table_constraints 
                    WHERE table_name = 'users' AND constraint_type = 'PRIMARY KEY'
                """))
                
                if pk_result.fetchone():
                    # Add as regular column
                    conn.execute(text("ALTER TABLE users ADD COLUMN id SERIAL"))
                else:
                    # Add as primary key
                    conn.execute(text("ALTER TABLE users ADD COLUMN id SERIAL PRIMARY KEY"))
                print("✅ Added id column")
            
            # 2. Create user with id=1
            print("📝 Ensuring paper trading user exists...")
            conn.execute(text("""
                INSERT INTO users (
                    username, email, password_hash, full_name,
                    initial_capital, current_balance, risk_tolerance,
                    is_active, zerodha_client_id, trading_enabled,
                    max_daily_trades, max_position_size, created_at, updated_at
                ) 
                SELECT 
                    'PAPER_TRADER_001', 'paper@algoauto.com',
                    '$2b$12$dummy', 'Paper Trading Account',
                    100000, 100000, 'medium',
                    true, 'PAPER', true,
                    1000, 500000, NOW(), NOW()
                WHERE NOT EXISTS (
                    SELECT 1 FROM users WHERE username = 'PAPER_TRADER_001'
                )
            """))
            
            # 3. Update to have id=1
            conn.execute(text("""
                UPDATE users SET id = 1 
                WHERE username = 'PAPER_TRADER_001' 
                AND id != 1
                AND NOT EXISTS (SELECT 1 FROM users WHERE id = 1)
            """))
            
            # 4. Verify
            result = conn.execute(text("SELECT id, username FROM users WHERE id = 1"))
            row = result.fetchone()
            if row:
                print(f"✅ User with id=1 exists: {row[1]}")
                return True
            else:
                print("❌ Failed to create user with id=1")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Running emergency database fix...")
    if fix_database():
        print("✅ Database fixed! Paper trades will now be saved.")
    else:
        print("❌ Fix failed. Check the errors above.") 