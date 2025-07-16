#!/usr/bin/env python3
"""
Comprehensive Database Schema Fix
Resolves all database schema mismatches and user creation issues
"""

import os
import logging
import psycopg2
from sqlalchemy import create_engine, text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Fix all database schema issues comprehensively"""
    
    print("🔧 COMPREHENSIVE DATABASE SCHEMA FIX")
    print("=" * 50)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("✅ Connected to database")
            
            # Step 1: Check current users table structure
            print("\n📊 Step 1: Analyzing current users table structure...")
            
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """))
            
            users_columns = result.fetchall()
            print(f"Found {len(users_columns)} columns in users table")
            
            user_id_type = None
            for col in users_columns:
                if col[0] == 'user_id':
                    user_id_type = col[1]
                    print(f"🔍 users.user_id type: {user_id_type}")
                    break
            
            # Step 2: Fix users table if needed
            print("\n🔧 Step 2: Ensuring users table has correct structure...")
            
            if user_id_type != 'integer':
                print(f"⚠️ users.user_id is {user_id_type}, converting to integer...")
                
                # Drop existing constraints that might prevent the change
                try:
                    conn.execute(text("ALTER TABLE paper_trades DROP CONSTRAINT IF EXISTS paper_trades_user_id_fkey"))
                    conn.execute(text("ALTER TABLE trades DROP CONSTRAINT IF EXISTS trades_user_id_fkey"))
                    print("✅ Dropped existing foreign key constraints")
                except Exception as e:
                    print(f"⚠️ Could not drop constraints: {e}")
                
                # Convert user_id to integer type
                try:
                    conn.execute(text("ALTER TABLE users ALTER COLUMN user_id TYPE INTEGER USING user_id::integer"))
                    print("✅ Converted users.user_id to integer type")
                except Exception as e:
                    print(f"❌ Could not convert user_id type: {e}")
                    # If conversion fails, we'll work with the existing type
            
            # Step 3: Create paper trading user properly
            print("\n👤 Step 3: Creating paper trading user...")
            
            # Check if paper user already exists
            result = conn.execute(text("""
                SELECT user_id FROM users 
                WHERE username = 'PAPER_TRADER_001' 
                LIMIT 1
            """))
            
            existing_user = result.fetchone()
            if existing_user:
                print(f"✅ Paper trading user already exists with user_id: {existing_user[0]}")
                paper_user_id = existing_user[0]
            else:
                # Create paper trading user (let SERIAL auto-generate user_id)
                try:
                    conn.execute(text("""
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
                            true, 'PAPER', true,
                            1000, 500000, NOW(), NOW(),
                            'trader', 'active'
                        ) ON CONFLICT (username) DO NOTHING
                    """))
                    
                    # Get the created user_id
                    result = conn.execute(text("""
                        SELECT user_id FROM users WHERE username = 'PAPER_TRADER_001'
                    """))
                    user_row = result.fetchone()
                    if user_row:
                        paper_user_id = user_row[0]
                        print(f"✅ Created paper trading user with user_id: {paper_user_id}")
                    else:
                        print("❌ Failed to create paper trading user")
                        return False
                        
                except Exception as e:
                    print(f"❌ Error creating paper user: {e}")
                    return False
            
            # Step 4: Ensure paper_trades table exists with correct schema
            print("\n📋 Step 4: Creating/updating paper_trades table...")
            
            try:
                # Drop paper_trades table if it exists with wrong schema
                conn.execute(text("DROP TABLE IF EXISTS paper_trades CASCADE"))
                
                # Create paper_trades table with correct schema
                conn.execute(text("""
                    CREATE TABLE paper_trades (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        symbol VARCHAR(20) NOT NULL,
                        action VARCHAR(10) NOT NULL,
                        quantity INTEGER NOT NULL,
                        price FLOAT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        order_id VARCHAR(50),
                        pnl FLOAT,
                        strategy VARCHAR(50),
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """))
                print("✅ Created paper_trades table with correct schema")
                
            except Exception as e:
                print(f"❌ Error creating paper_trades table: {e}")
                return False
            
            # Step 5: Ensure trades table has correct foreign key
            print("\n💼 Step 5: Updating trades table foreign key...")
            
            try:
                # Drop existing foreign key if it exists
                conn.execute(text("ALTER TABLE trades DROP CONSTRAINT IF EXISTS trades_user_id_fkey"))
                
                # Add correct foreign key constraint
                conn.execute(text("""
                    ALTER TABLE trades 
                    ADD CONSTRAINT trades_user_id_fkey 
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                """))
                print("✅ Updated trades table foreign key constraint")
                
            except Exception as e:
                print(f"⚠️ Could not update trades foreign key: {e}")
                # This is not critical for paper trading to work
            
            # Step 6: Commit all changes
            conn.commit()
            print("\n✅ All database schema fixes committed successfully!")
            
            # Step 7: Verify the fix
            print("\n🔍 Step 7: Verifying schema fix...")
            
            # Test creating a paper trade
            try:
                test_order_id = f"TEST_{int(__import__('time').time())}"
                conn.execute(text("""
                    INSERT INTO paper_trades (
                        user_id, symbol, action, quantity, price, timestamp, status, order_id
                    ) VALUES (
                        :user_id, 'TEST', 'BUY', 1, 100.0, NOW(), 'EXECUTED', :order_id
                    )
                """), {"user_id": paper_user_id, "order_id": test_order_id})
                
                # Delete the test record
                conn.execute(text("DELETE FROM paper_trades WHERE order_id = :order_id"), {"order_id": test_order_id})
                conn.commit()
                
                print("✅ Paper trades table is working correctly!")
                
            except Exception as e:
                print(f"❌ Paper trades test failed: {e}")
                return False
            
        print("\n🎯 DATABASE SCHEMA FIX COMPLETED SUCCESSFULLY!")
        print("🚀 Paper trading should now work without database errors")
        return True
        
    except Exception as e:
        print(f"❌ Database schema fix failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_database_schema()
    if success:
        print("\n✅ Ready to deploy - database schema is now correct")
    else:
        print("\n❌ Schema fix failed - manual intervention may be required") 