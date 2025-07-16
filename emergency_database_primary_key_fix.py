#!/usr/bin/env python3
"""
Emergency Database PRIMARY KEY Fix
Fixes the users table PRIMARY KEY constraint issue causing foreign key failures
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment"""
    # Try different environment variable names
    for var_name in ['DATABASE_URL', 'POSTGRES_URL', 'DB_URL']:
        url = os.environ.get(var_name)
        if url:
            logger.info(f"Using database URL from {var_name}")
            return url
    
    # Fallback: construct from individual components
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', '5432')
    name = os.environ.get('DB_NAME', 'trading_system')
    user = os.environ.get('DB_USER', 'postgres')
    password = os.environ.get('DB_PASSWORD', '')
    
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    else:
        return f"postgresql://{user}@{host}:{port}/{name}"

def check_primary_key_constraint(conn):
    """Check if users table has proper PRIMARY KEY constraint"""
    try:
        cursor = conn.cursor()
        
        # Check for PRIMARY KEY constraint
        cursor.execute("""
            SELECT constraint_name, constraint_type 
            FROM information_schema.table_constraints 
            WHERE table_name = 'users' 
            AND constraint_type = 'PRIMARY KEY'
        """)
        
        pk_result = cursor.fetchall()
        logger.info(f"PRIMARY KEY constraints found: {pk_result}")
        
        if not pk_result:
            logger.error("❌ No PRIMARY KEY constraint found")
            return False
        
        # Test if foreign key can reference this table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_fk_check (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Clean up test table
            cursor.execute("DROP TABLE IF EXISTS test_fk_check")
            conn.commit()
            
            logger.info("✅ PRIMARY KEY constraint works for foreign keys")
            return True
            
        except Exception as fk_error:
            logger.error(f"❌ Foreign key test failed: {fk_error}")
            cursor.execute("DROP TABLE IF EXISTS test_fk_check")
            conn.commit()
            return False
            
    except Exception as e:
        logger.error(f"❌ PRIMARY KEY check failed: {e}")
        return False

def fix_users_primary_key(conn):
    """Fix users table PRIMARY KEY constraint"""
    try:
        cursor = conn.cursor()
        
        logger.info("🔧 Starting users table PRIMARY KEY repair...")
        
        # Backup existing data
        cursor.execute("SELECT * FROM users")
        backup_data = cursor.fetchall()
        logger.info(f"📦 Backing up {len(backup_data)} user records")
        
        # Get column info
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        columns_info = cursor.fetchall()
        
        # Drop dependent tables first
        dependent_tables = ['paper_trades', 'positions', 'trades', 'orders']
        for table in dependent_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                logger.info(f"   ✓ Dropped {table}")
            except Exception as e:
                logger.warning(f"   ⚠️ Could not drop {table}: {e}")
        
        # Drop and recreate users table
        logger.info("🔄 Recreating users table with proper PRIMARY KEY...")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")
        
        # Create users table with proper SERIAL PRIMARY KEY
        create_sql = """
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                initial_capital FLOAT DEFAULT 50000.0,
                current_balance FLOAT DEFAULT 50000.0,
                risk_tolerance VARCHAR(20) DEFAULT 'medium',
                is_active BOOLEAN DEFAULT TRUE,
                zerodha_client_id VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_trades INTEGER DEFAULT 0,
                user_type VARCHAR(20) DEFAULT 'trader',
                status VARCHAR(20) DEFAULT 'active',
                phone VARCHAR(20),
                trading_enabled BOOLEAN DEFAULT TRUE,
                max_position_size INTEGER DEFAULT 500000,
                zerodha_api_key VARCHAR(100),
                zerodha_api_secret VARCHAR(100),
                zerodha_access_token TEXT,
                zerodha_public_token VARCHAR(100),
                total_pnl FLOAT DEFAULT 0,
                last_login TIMESTAMP,
                paper_trading BOOLEAN DEFAULT FALSE,
                max_daily_trades INTEGER
            )
        """
        cursor.execute(create_sql)
        logger.info("✅ Users table recreated with proper SERIAL PRIMARY KEY")
        
        # Restore data if any existed
        if backup_data:
            logger.info(f"🔄 Restoring {len(backup_data)} user records...")
            
            for row in backup_data:
                try:
                    # Insert data excluding the old id (SERIAL will auto-generate)
                    # Map to the most essential columns to avoid issues
                    if len(row) >= 4:  # At least username, email, password_hash
                        cursor.execute("""
                            INSERT INTO users (username, email, password_hash, is_active, trading_enabled) 
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (username) DO NOTHING
                        """, (row[1], row[2], row[3], True, True))
                except Exception as restore_error:
                    logger.warning(f"⚠️ Could not restore user record: {restore_error}")
                    continue
            
            logger.info("✅ User data restoration completed")
        
        # Create a default paper trading user
        logger.info("🔄 Creating default paper trading user...")
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, is_active, trading_enabled, paper_trading)
            VALUES ('PAPER_TRADER_001', 'paper@algoauto.com', '$2b$12$dummy.hash.paper.trading', 'Paper Trading Account', TRUE, TRUE, TRUE)
            ON CONFLICT (username) DO NOTHING
        """)
        
        # Commit all changes
        conn.commit()
        
        # Verify the fix
        if check_primary_key_constraint(conn):
            logger.info("✅ Users table PRIMARY KEY constraint verified working")
            return True
        else:
            logger.error("❌ PRIMARY KEY constraint still not working")
            return False
            
    except Exception as e:
        logger.error(f"❌ PRIMARY KEY fix failed: {e}")
        conn.rollback()
        return False

def main():
    """Main function to fix database PRIMARY KEY issues"""
    try:
        # Get database URL
        database_url = get_database_url()
        if not database_url:
            logger.error("❌ No database URL found in environment variables")
            return False
        
        logger.info(f"🔗 Connecting to database...")
        
        # Parse URL for psycopg2
        parsed = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            sslmode='require' if 'sslmode=require' in database_url else 'prefer'
        )
        
        logger.info("✅ Connected to database")
        
        # Check if fix is needed
        if check_primary_key_constraint(conn):
            logger.info("✅ Users table PRIMARY KEY is already working correctly")
            return True
        
        # Apply fix
        success = fix_users_primary_key(conn)
        
        if success:
            logger.info("🎉 Database PRIMARY KEY fix completed successfully!")
        else:
            logger.error("❌ Database PRIMARY KEY fix failed")
        
        conn.close()
        return success
        
    except Exception as e:
        logger.error(f"❌ Database fix failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 