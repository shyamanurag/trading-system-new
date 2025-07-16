#!/usr/bin/env python3
"""
Emergency Schema Fix for Production
Fixes the specific foreign key constraint issues in production database
"""
import sys
import os
import logging
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_production_database_engine():
    """Get production database engine"""
    try:
        # Add src to path for imports
        sys.path.insert(0, 'src')
        from config.database import db_config
        database_url = db_config.database_url
        logger.info("Using database URL from config")
    except Exception as e:
        # Fallback to environment variable
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("No database URL available")
        logger.info("Using database URL from environment")
    
    # Ensure SSL configuration for production
    if 'postgresql' in database_url and 'ondigitalocean.com' in database_url:
        connect_args = {'sslmode': 'require'}
    else:
        connect_args = {}
    
    engine = create_engine(database_url, connect_args=connect_args)
    return engine

def fix_users_table_schema(engine):
    """Fix users table to have proper primary key"""
    with engine.begin() as conn:
        logger.info("🔧 Fixing users table schema...")
        
        # Check if users table has id column
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'id'
        """))
        
        id_column = result.fetchone()
        has_id_column = id_column is not None
        
        logger.info(f"Users table has id column: {has_id_column}")
        if has_id_column:
            logger.info(f"ID column details: {id_column}")
        
        # Check for primary key constraints
        result = conn.execute(text("""
            SELECT 
                tc.constraint_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'users' 
            AND tc.constraint_type = 'PRIMARY KEY'
        """))
        
        primary_keys = result.fetchall()
        logger.info(f"Existing primary keys: {primary_keys}")
        
        # Fix the table structure
        if not has_id_column:
            logger.info("Adding id column as primary key...")
            conn.execute(text("ALTER TABLE users ADD COLUMN id SERIAL PRIMARY KEY"))
            logger.info("✅ Added id column as primary key")
            
        elif has_id_column and not primary_keys:
            logger.info("Adding primary key constraint to existing id column...")
            # First ensure id column has values
            conn.execute(text("UPDATE users SET id = DEFAULT WHERE id IS NULL"))
            conn.execute(text("ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (id)"))
            logger.info("✅ Added primary key constraint")
            
        elif primary_keys and primary_keys[0][1] != 'id':
            logger.info(f"Changing primary key from {primary_keys[0][1]} to id...")
            # Drop existing primary key
            conn.execute(text(f"ALTER TABLE users DROP CONSTRAINT {primary_keys[0][0]}"))
            # Ensure id has values
            conn.execute(text("UPDATE users SET id = DEFAULT WHERE id IS NULL"))
            # Add new primary key
            conn.execute(text("ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (id)"))
            logger.info("✅ Changed primary key to id")
        else:
            logger.info("✅ Users table already has proper id primary key")
        
        # Ensure all users have id values
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE id IS NULL"))
        null_ids = result.scalar()
        
        if null_ids > 0:
            logger.info(f"Fixing {null_ids} users with NULL id values...")
            conn.execute(text("UPDATE users SET id = DEFAULT WHERE id IS NULL"))
            logger.info("✅ Fixed NULL id values")

def fix_paper_trades_table(engine):
    """Fix paper_trades table with proper foreign key"""
    with engine.begin() as conn:
        logger.info("🔧 Fixing paper_trades table...")
        
        # Drop and recreate paper_trades table with proper foreign key
        logger.info("Dropping existing paper_trades table...")
        conn.execute(text("DROP TABLE IF EXISTS paper_trades CASCADE"))
        
        logger.info("Creating paper_trades table with proper foreign key...")
        conn.execute(text("""
            CREATE TABLE paper_trades (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                symbol VARCHAR(20) NOT NULL,
                action VARCHAR(10) NOT NULL,
                quantity INTEGER NOT NULL,
                price FLOAT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                status VARCHAR(20) NOT NULL,
                order_id VARCHAR(50),
                pnl FLOAT,
                strategy VARCHAR(50),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        logger.info("✅ Created paper_trades table with proper foreign key")

def create_default_paper_user(engine):
    """Create default paper trading user"""
    with engine.begin() as conn:
        logger.info("🔧 Creating default paper trading user...")
        
        # Check if default user exists
        result = conn.execute(text("""
            SELECT id FROM users WHERE username = 'PAPER_TRADER_001'
        """))
        
        existing_user = result.fetchone()
        
        if existing_user:
            logger.info(f"✅ Default paper trading user already exists with id: {existing_user[0]}")
        else:
            # Create default user
            conn.execute(text("""
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
                )
            """))
            
            logger.info("✅ Created default paper trading user")

def verify_fixes(engine):
    """Verify that all fixes worked correctly"""
    with engine.connect() as conn:
        logger.info("🔍 Verifying fixes...")
        
        # Verify users table primary key
        result = conn.execute(text("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'users' 
            AND tc.constraint_type = 'PRIMARY KEY'
        """))
        
        pk_columns = [row[0] for row in result.fetchall()]
        logger.info(f"✅ Users table primary key columns: {pk_columns}")
        
        # Verify paper_trades foreign key
        result = conn.execute(text("""
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
        """))
        
        fk_constraints = result.fetchall()
        logger.info(f"✅ Paper trades foreign key constraints: {len(fk_constraints)}")
        for fk in fk_constraints:
            logger.info(f"   {fk[1]} -> {fk[2]}.{fk[3]}")
        
        # Count users
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        logger.info(f"✅ Total users in database: {user_count}")

def main():
    """Main function to run all fixes"""
    logger.info("🚨 EMERGENCY SCHEMA FIX STARTING...")
    
    try:
        engine = get_production_database_engine()
        logger.info("✅ Database connection established")
        
        # Apply fixes in order
        fix_users_table_schema(engine)
        fix_paper_trades_table(engine)
        create_default_paper_user(engine)
        verify_fixes(engine)
        
        logger.info("🎉 ALL FIXES COMPLETED SUCCESSFULLY!")
        logger.info("The foreign key constraint errors should now be resolved.")
        
    except Exception as e:
        logger.error(f"❌ Emergency fix failed: {e}")
        raise

if __name__ == "__main__":
    main() 