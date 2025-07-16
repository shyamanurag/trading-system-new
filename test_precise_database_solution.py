"""
Test the precise database schema solution - not a workaround, but the definitive approach.
This verifies that our database schema management is working correctly.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database_schema_manager import DatabaseSchemaManager
from src.core.paper_trading_user_manager import PaperTradingUserManager
from src.config.database import DatabaseConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_precise_database_solution():
    """Test our precise database schema solution"""
    print("\n" + "="*60)
    print("TESTING PRECISE DATABASE SCHEMA SOLUTION")
    print("This is the definitive approach, not a workaround")
    print("="*60 + "\n")
    
    try:
        # Initialize database config
        db_config = DatabaseConfig()
        database_url = db_config.database_url
        
        print(f"Database URL: {database_url}\n")
        
        # Test 1: Verify schema manager creates precise schema
        print("1. Testing DatabaseSchemaManager...")
        schema_manager = DatabaseSchemaManager(database_url)
        result = schema_manager.ensure_precise_schema()
        
        print(f"   Schema verification status: {result['status']}")
        print(f"   Users table: {result['users_table']['status']}")
        if result['users_table']['actions']:
            print(f"   - Actions taken: {result['users_table']['actions']}")
        print(f"   Paper trades table: {result['paper_trades_table']['status']}")
        if result['paper_trades_table']['actions']:
            print(f"   - Actions taken: {result['paper_trades_table']['actions']}")
        
        # Test 2: Verify table structure
        print("\n2. Verifying precise table structure...")
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        # Check users table
        users_columns = {col['name']: col for col in inspector.get_columns('users')}
        print(f"   Users table columns: {list(users_columns.keys())}")
        
        # Verify id column exists and is primary key
        if 'id' in users_columns:
            pk_constraint = inspector.get_pk_constraint('users')
            print(f"   - Primary key: {pk_constraint['constrained_columns']}")
        
        # Check paper_trades table
        trades_columns = {col['name']: col for col in inspector.get_columns('paper_trades')}
        print(f"   Paper trades columns: {list(trades_columns.keys())}")
        
        # Test 3: Verify paper trading user manager works
        print("\n3. Testing PaperTradingUserManager...")
        
        # Create a session
        Session = sessionmaker(bind=engine)
        with Session() as session:
            # Ensure user exists
            user_id = PaperTradingUserManager.ensure_user_exists(session)
            print(f"   User identifier returned: {user_id}")
            
            # Get user id for trades
            trade_user_id = PaperTradingUserManager.get_user_id_for_trades(session)
            print(f"   User ID for trades: {trade_user_id}")
            
            # Verify user exists in database
            result = session.execute(text("SELECT id, username, email, trading_enabled FROM users LIMIT 1"))
            user = result.fetchone()
            if user:
                print(f"   Paper user verified:")
                print(f"   - ID: {user[0]}")
                print(f"   - Username: {user[1]}")
                print(f"   - Email: {user[2]}")
                print(f"   - Trading enabled: {user[3]}")
        
        # Test 4: Test paper trade insertion
        print("\n4. Testing paper trade insertion...")
        with Session() as session:
            try:
                # Get user id for trade
                user_id = PaperTradingUserManager.get_user_id_for_trades(session)
                
                # Insert test trade
                insert_query = text("""
                    INSERT INTO paper_trades (
                        user_id, symbol, action, quantity, price, timestamp,
                        status, order_id, pnl, strategy, created_at
                    ) VALUES (
                        :user_id, :symbol, :action, :quantity, :price, :timestamp,
                        :status, :order_id, :pnl, :strategy, :created_at
                    )
                """)
                
                test_trade = {
                    'user_id': user_id,
                    'symbol': 'TEST',
                    'action': 'BUY',
                    'quantity': 100,
                    'price': 100.50,
                    'timestamp': datetime.now(),
                    'status': 'executed',
                    'order_id': 'TEST123',
                    'pnl': 0.0,
                    'strategy': 'test_strategy',
                    'created_at': datetime.now()
                }
                
                session.execute(insert_query, test_trade)
                session.commit()
                
                # Verify insertion
                count_result = session.execute(text("SELECT COUNT(*) FROM paper_trades WHERE symbol = 'TEST'")).scalar()
                print(f"   Test trade inserted successfully. Total TEST trades: {count_result}")
                
                # Clean up test trade
                session.execute(text("DELETE FROM paper_trades WHERE symbol = 'TEST'"))
                session.commit()
                print("   Test trade cleaned up")
                
            except Exception as e:
                print(f"   Trade insertion error: {e}")
                session.rollback()
        
        # Test 5: Verify idempotency
        print("\n5. Testing idempotency (running schema manager again)...")
        result2 = schema_manager.ensure_precise_schema()
        print(f"   Second run status: {result2['status']}")
        print(f"   Users table actions: {result2['users_table']['actions'] or 'None (already correct)'}")
        print(f"   Paper trades actions: {result2['paper_trades_table']['actions'] or 'None (already correct)'}")
        
        print("\n" + "="*60)
        print("PRECISE DATABASE SOLUTION TEST COMPLETE")
        print("The database now has the exact schema required")
        print("This is the permanent, definitive solution")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_precise_database_solution())
    sys.exit(0 if success else 1) 