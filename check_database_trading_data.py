#!/usr/bin/env python3
"""
Database Trading Data Check Script
Verifies if autonomous trading data is being stored in the database.
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import asyncpg
import asyncio

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.database import get_db, engine
    from src.models.trading_models import User, Position, Trade, Order, UserMetric, TradingSession
    print("✅ Successfully imported database models")
except ImportError as e:
    print(f"❌ Error importing models: {e}")
    print("🔍 Trying alternative database connection...")

def get_database_url():
    """Get database URL from environment or config"""
    # Try different sources for database URL
    db_url = (
        os.getenv('DATABASE_URL') or 
        os.getenv('DB_URL') or
        os.getenv('POSTGRES_URL') or
        'postgresql://postgres:password@localhost:5432/trading_system'
    )
    return db_url

async def check_database_async():
    """Check database using asyncpg for direct connection"""
    print("🔍 Checking database connection with asyncpg...")
    
    db_url = get_database_url()
    
    try:
        # Parse URL for asyncpg
        if db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', '')
        elif db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', '')
            
        # Extract connection parts
        if '@' in db_url:
            auth_part, host_part = db_url.split('@', 1)
            if ':' in auth_part:
                user, password = auth_part.split(':', 1)
            else:
                user, password = auth_part, ''
                
            if '/' in host_part:
                host_port, database = host_part.split('/', 1)
            else:
                host_port, database = host_part, 'trading_system'
                
            if ':' in host_port:
                host, port = host_port.split(':', 1)
                port = int(port)
            else:
                host, port = host_port, 5432
        else:
            # Default values
            host, port, user, password, database = 'localhost', 5432, 'postgres', 'password', 'trading_system'
        
        print(f"📊 Connecting to: {host}:{port}/{database} as {user}")
        
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        print("✅ Database connection successful!")
        
        # Check if tables exist
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('users', 'trades', 'positions', 'orders', 'user_metrics', 'trading_sessions')
        ORDER BY table_name;
        """
        
        tables = await conn.fetch(tables_query)
        print(f"📋 Found {len(tables)} trading tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # Check data in each table
        print("\n📊 DATA ANALYSIS:")
        
        table_queries = {
            'users': 'SELECT COUNT(*) as count, MAX(created_at) as latest FROM users',
            'trades': 'SELECT COUNT(*) as count, MAX(executed_at) as latest, SUM(CASE WHEN trade_type = \'buy\' THEN 1 ELSE 0 END) as buys, SUM(CASE WHEN trade_type = \'sell\' THEN 1 ELSE 0 END) as sells FROM trades',
            'positions': 'SELECT COUNT(*) as count, COUNT(CASE WHEN status = \'open\' THEN 1 END) as open_positions, SUM(realized_pnl) as total_realized_pnl FROM positions',
            'orders': 'SELECT COUNT(*) as count, COUNT(CASE WHEN status = \'FILLED\' THEN 1 END) as filled_orders FROM orders',
            'user_metrics': 'SELECT COUNT(*) as count, MAX(date) as latest_date FROM user_metrics',
            'trading_sessions': 'SELECT COUNT(*) as count, COUNT(CASE WHEN status = \'ACTIVE\' THEN 1 END) as active_sessions, MAX(session_start) as latest_session FROM trading_sessions'
        }
        
        for table_name, query in table_queries.items():
            try:
                result = await conn.fetchrow(query)
                if result:
                    print(f"\n🗂️  {table_name.upper()}:")
                    for key, value in result.items():
                        if value is not None:
                            print(f"   {key}: {value}")
                        else:
                            print(f"   {key}: No data")
                else:
                    print(f"\n🗂️  {table_name.upper()}: No data")
            except Exception as e:
                print(f"\n❌ Error querying {table_name}: {e}")
        
        # Check for recent trading activity (last 24 hours)
        print("\n🕐 RECENT ACTIVITY (Last 24 hours):")
        recent_queries = {
            'Recent Trades': "SELECT COUNT(*) FROM trades WHERE executed_at >= NOW() - INTERVAL '24 hours'",
            'Recent Orders': "SELECT COUNT(*) FROM orders WHERE created_at >= NOW() - INTERVAL '24 hours'",
            'Recent Position Updates': "SELECT COUNT(*) FROM positions WHERE updated_at >= NOW() - INTERVAL '24 hours'"
        }
        
        for description, query in recent_queries.items():
            try:
                result = await conn.fetchval(query)
                print(f"   {description}: {result or 0}")
            except Exception as e:
                print(f"   {description}: Error - {e}")
        
        # Check if autonomous trading data exists
        print("\n🤖 AUTONOMOUS TRADING CHECK:")
        autonomous_queries = {
            'Trades with strategy field': "SELECT COUNT(*) FROM trades WHERE strategy IS NOT NULL",
            'Positions with strategy': "SELECT COUNT(*) FROM positions WHERE strategy IS NOT NULL",
            'Active trading sessions': "SELECT COUNT(*) FROM trading_sessions WHERE status = 'ACTIVE'",
            'Paper trading users': "SELECT COUNT(*) FROM users WHERE zerodha_client_id LIKE '%PAPER%' OR username LIKE '%PAPER%'"
        }
        
        for description, query in autonomous_queries.items():
            try:
                result = await conn.fetchval(query)
                print(f"   {description}: {result or 0}")
            except Exception as e:
                print(f"   {description}: Error - {e}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_database_sync():
    """Check database using SQLAlchemy (sync)"""
    print("🔍 Checking database with SQLAlchemy...")
    
    try:
        db_url = get_database_url()
        engine = create_engine(db_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ SQLAlchemy connection successful!")
            
            # Check table existence
            tables_result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'trades', 'positions', 'orders', 'user_metrics')
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in tables_result]
            print(f"📋 Found tables: {', '.join(tables)}")
            
            # Basic counts
            for table in tables:
                try:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    print(f"   {table}: {count} records")
                except Exception as e:
                    print(f"   {table}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False

def main():
    """Main function to run database checks"""
    print("=" * 60)
    print("🗄️  DATABASE TRADING DATA VERIFICATION")
    print("=" * 60)
    print(f"🕐 Timestamp: {datetime.now()}")
    print(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Try async connection first
    try:
        success = asyncio.run(check_database_async())
        if success:
            print("\n✅ Async database check completed successfully!")
        else:
            print("\n⚠️ Async check failed, trying sync method...")
            success = check_database_sync()
    except Exception as e:
        print(f"\n❌ Async check error: {e}")
        print("⚠️ Trying sync method...")
        success = check_database_sync()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 DATABASE CHECK COMPLETE!")
        print("\n💡 INTERPRETATION:")
        print("   • If you see 0 records in trading tables, data is stored in memory only")
        print("   • If you see data, your autonomous trading is persisting to database")
        print("   • Recent activity shows if trading happened in last 24 hours")
        print("   • Check autonomous trading fields for strategy-based trades")
    else:
        print("❌ DATABASE CHECK FAILED!")
        print("\n🔧 TROUBLESHOOTING:")
        print("   • Check if PostgreSQL is running")
        print("   • Verify database credentials in environment variables")
        print("   • Ensure database 'trading_system' exists")
        print("   • Run database migrations if needed")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 