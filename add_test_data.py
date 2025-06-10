import asyncio
import os
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv('production.env')

# Add the project root to Python path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager

async def add_test_data():
    """Add test data to the database"""
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    try:
        # Add test users
        users = [
            {
                'username': 'test_trader1',
                'name': 'Test Trader 1',
                'email': 'trader1@test.com',
                'role': 'trader',
                'is_active': True,
                'capital_allocated': 100000.0,
                'risk_limit': 5000.0,
                'daily_loss_limit': 2000.0
            },
            {
                'username': 'test_trader2',
                'name': 'Test Trader 2',
                'email': 'trader2@test.com',
                'role': 'trader',
                'is_active': True,
                'capital_allocated': 150000.0,
                'risk_limit': 7500.0,
                'daily_loss_limit': 3000.0
            }
        ]
        
        user_ids = []
        for user_data in users:
            user_id = await db_manager.create_user(user_data)
            user_ids.append(user_id)
            print(f"Created user: {user_data['name']} (ID: {user_id})")
        
        # Add test trades
        symbols = ['RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK']
        
        for user_id in user_ids:
            # Add some completed trades
            for i in range(10):
                trade_date = datetime.now() - timedelta(days=random.randint(1, 30))
                entry_price = random.uniform(1000, 3000)
                exit_price = entry_price * (1 + random.uniform(-0.05, 0.05))
                quantity = random.randint(10, 100)
                
                trade_data = {
                    'user_id': user_id,
                    'symbol': random.choice(symbols),
                    'strategy': random.choice(['momentum', 'mean_reversion', 'breakout']),
                    'direction': random.choice(['long', 'short']),
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'quantity': quantity,
                    'entry_time': trade_date,
                    'exit_time': trade_date + timedelta(hours=random.randint(1, 6)),
                    'pnl': (exit_price - entry_price) * quantity,
                    'status': 'closed',
                    'trade_type': 'paper'
                }
                
                await db_manager.record_trade(trade_data)
            
            # Add some open positions
            for i in range(3):
                position_data = {
                    'user_id': user_id,
                    'symbol': random.choice(symbols),
                    'quantity': random.randint(10, 50),
                    'entry_price': random.uniform(1000, 3000),
                    'current_price': random.uniform(1000, 3000),
                    'position_type': random.choice(['long', 'short']),
                    'strategy': random.choice(['momentum', 'mean_reversion']),
                    'opened_at': datetime.now() - timedelta(hours=random.randint(1, 24))
                }
                
                await db_manager.update_position(
                    user_id,
                    position_data['symbol'],
                    position_data['quantity'],
                    position_data['entry_price'],
                    position_data['current_price']
                )
        
        print("\nTest data added successfully!")
        
        # Verify data
        summary = await db_manager.get_system_summary()
        print(f"\nSystem Summary:")
        print(f"Total Users: {summary.get('total_users', 0)}")
        print(f"Total Trades: {summary.get('total_trades', 0)}")
        print(f"Total P&L: {summary.get('total_pnl', 0)}")
        
    except Exception as e:
        print(f"Error adding test data: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(add_test_data()) 