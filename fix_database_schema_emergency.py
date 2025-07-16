#!/usr/bin/env python3
"""
Emergency Database Schema Fix - Fixes the persistent foreign key constraint errors
"""
import os
import psycopg2
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get database connection from environment"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Parse the URL
    url = urlparse(database_url)
    
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        database=url.path[1:],  # Remove leading slash
        user=url.username,
        password=url.password,
        sslmode='require'
    )
    return conn

def fix_database_schema():
    """Apply emergency database schema fixes"""
    logger.info("🚨 EMERGENCY DATABASE SCHEMA FIX")
    
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        logger.info("Starting transaction...")
        
        # Step 1: Check current users table structure
        logger.info("📋 Checking current users table structure...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        has_id_column = any(col[0] == 'id' for col in columns)
        
        logger.info(f"Current users table columns: {[col[0] for col in columns]}")
        logger.info(f"Has id column: {has_id_column}")
        
        # Step 2: Check for primary key
        cursor.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'users' 
            AND tc.constraint_type = 'PRIMARY KEY'
        """)
        
        pk_columns = cursor.fetchall()
        has_primary_key = len(pk_columns) > 0
        
        logger.info(f"Primary key columns: {[col[0] for col in pk_columns]}")
        logger.info(f"Has primary key: {has_primary_key}")
        
        # Step 3: Fix users table structure if needed
        if not has_id_column:
            logger.info("🔧 Adding id column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN id SERIAL PRIMARY KEY")
            logger.info("✅ Added id column as primary key")
            
        elif has_id_column and not has_primary_key:
            logger.info("🔧 Adding primary key constraint to id column...")
            cursor.execute("ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (id)")
            logger.info("✅ Added primary key constraint to id column")
            
        elif has_primary_key and pk_columns[0][0] != 'id':
            logger.info(f"🔧 Changing primary key from {pk_columns[0][0]} to id...")
            # Drop existing primary key
            cursor.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'users' AND constraint_type = 'PRIMARY KEY'
            """)
            pk_constraint = cursor.fetchone()
            if pk_constraint:
                cursor.execute(f"ALTER TABLE users DROP CONSTRAINT {pk_constraint[0]}")
            
            # Make id the primary key
            cursor.execute("ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (id)")
            logger.info("✅ Changed primary key to id column")
        
        # Step 4: Ensure id values exist for all users
        logger.info("🔧 Updating NULL id values...")
        cursor.execute("UPDATE users SET id = nextval('users_id_seq') WHERE id IS NULL")
        rows_updated = cursor.rowcount
        logger.info(f"✅ Updated {rows_updated} users with NULL id values")
        
        # Step 5: Drop and recreate paper_trades table with proper foreign key
        logger.info("🔧 Recreating paper_trades table with proper foreign key...")
        cursor.execute("DROP TABLE IF EXISTS paper_trades CASCADE")
        
        cursor.execute("""
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
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        logger.info("✅ Created paper_trades table with proper foreign key")
        
        # Step 6: Create default paper trading user if it doesn't exist
        logger.info("🔧 Creating default paper trading user...")
        cursor.execute("""
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
                1000, 500000, NOW(), NOW()
            ) ON CONFLICT (username) DO NOTHING
        """)
        
        if cursor.rowcount > 0:
            logger.info("✅ Created default paper trading user")
        else:
            logger.info("ℹ️  Default paper trading user already exists")
        
        # Commit all changes
        conn.commit()
        logger.info("✅ ALL DATABASE SCHEMA FIXES APPLIED SUCCESSFULLY")
        
        # Verify the fixes
        logger.info("🔍 Verifying fixes...")
        
        # Check users table primary key
        cursor.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'users' 
            AND tc.constraint_type = 'PRIMARY KEY'
        """)
        
        pk_columns = cursor.fetchall()
        logger.info(f"✅ Users table primary key: {[col[0] for col in pk_columns]}")
        
        # Check paper_trades foreign key
        cursor.execute("""
            SELECT 
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu 
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = 'paper_trades'
        """)
        
        fk_constraints = cursor.fetchall()
        logger.info(f"✅ Paper trades foreign keys: {fk_constraints}")
        
        # Check user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        logger.info(f"✅ Total users in database: {user_count}")
        
    except Exception as e:
        logger.error(f"❌ Database fix failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_database_schema() 