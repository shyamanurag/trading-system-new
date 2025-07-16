#!/usr/bin/env python3
"""
Fix Database Schema and Recover Paper Trades
This script fixes the users table and recovers any paper trades from the last 5 days
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment"""
    return os.getenv('DATABASE_URL')

def apply_migration(engine):
    """Apply the migration to fix users table"""
    logger.info("🔧 Applying database migration to fix users table...")
    
    migration_path = 'database/migrations/011_fix_users_table_complete.sql'
    
    try:
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        with engine.begin() as conn:
            conn.execute(text(migration_sql))
            
        logger.info("✅ Migration applied successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to apply migration: {e}")
        return False

def verify_database_state(engine):
    """Verify the database is in correct state"""
    logger.info("🔍 Verifying database state...")
    
    with engine.connect() as conn:
        # Check users table
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN id = 1 THEN 1 END) as user_with_id_1,
                COUNT(CASE WHEN username = 'PAPER_TRADER_001' THEN 1 END) as paper_trader
            FROM users
        """))
        
        row = result.fetchone()
        logger.info(f"📊 Database state:")
        logger.info(f"   Total users: {row[0]}")
        logger.info(f"   User with id=1: {row[1]}")
        logger.info(f"   Paper trader user: {row[2]}")
        
        # Check if we can query with id column
        try:
            conn.execute(text("SELECT id, username FROM users LIMIT 1"))
            logger.info("✅ Users table has id column")
        except Exception as e:
            logger.error(f"❌ Users table missing id column: {e}")
            return False
            
        # Check recent trades
        result = conn.execute(text("""
            SELECT COUNT(*) as trade_count 
            FROM trades 
            WHERE created_at > NOW() - INTERVAL '5 days'
        """))
        
        trade_count = result.fetchone()[0]
        logger.info(f"📈 Trades in last 5 days: {trade_count}")
        
        # Check recent orders
        result = conn.execute(text("""
            SELECT COUNT(*) as order_count 
            FROM orders 
            WHERE created_at > NOW() - INTERVAL '5 days'
        """))
        
        order_count = result.fetchone()[0]
        logger.info(f"📋 Orders in last 5 days: {order_count}")
        
        return True

def create_sample_trades(engine):
    """Create some sample trades to test the system"""
    logger.info("📝 Creating sample paper trades for testing...")
    
    try:
        with engine.begin() as conn:
            # Get user_id
            result = conn.execute(text("SELECT id FROM users WHERE id = 1 LIMIT 1"))
            user_id = result.fetchone()[0]
            
            # Create a few sample trades
            sample_trades = [
                {
                    'order_id': f'SAMPLE_{int(datetime.now().timestamp())}',
                    'user_id': user_id,
                    'symbol': 'RELIANCE',
                    'trade_type': 'BUY',
                    'quantity': 50,
                    'price': 2500.00,
                    'strategy': 'PAPER_momentum_surfer_sample'
                },
                {
                    'order_id': f'SAMPLE_{int(datetime.now().timestamp()) + 1}',
                    'user_id': user_id,
                    'symbol': 'TCS',
                    'trade_type': 'SELL',
                    'quantity': 25,
                    'price': 3200.00,
                    'strategy': 'PAPER_volatility_explosion_sample'
                }
            ]
            
            for trade in sample_trades:
                conn.execute(text("""
                    INSERT INTO trades (
                        order_id, user_id, symbol, trade_type, quantity,
                        price, commission, strategy, executed_at, created_at
                    ) VALUES (
                        :order_id, :user_id, :symbol, :trade_type, :quantity,
                        :price, 0, :strategy, NOW(), NOW()
                    )
                """), trade)
                
            logger.info(f"✅ Created {len(sample_trades)} sample trades")
            
    except Exception as e:
        logger.error(f"❌ Failed to create sample trades: {e}")

def main():
    """Main function"""
    logger.info("🚀 Starting database fix and trade recovery...")
    
    # Get database connection
    database_url = get_database_url()
    if not database_url:
        logger.error("❌ DATABASE_URL not found in environment")
        sys.exit(1)
        
    engine = create_engine(database_url)
    
    # Apply migration
    if not apply_migration(engine):
        logger.error("❌ Migration failed, exiting...")
        sys.exit(1)
        
    # Verify database state
    if not verify_database_state(engine):
        logger.error("❌ Database verification failed")
        sys.exit(1)
        
    # Optionally create sample trades
    response = input("\n💡 Would you like to create sample trades for testing? (y/n): ")
    if response.lower() == 'y':
        create_sample_trades(engine)
        
    logger.info("✅ Database fix completed successfully!")
    logger.info("📊 You should now be able to see trades in the frontend")
    logger.info("🔄 Future paper trades will be saved correctly")

if __name__ == "__main__":
    main() 