#!/usr/bin/env python3
"""
Trading Data Persistence System
Prevents data loss during redeployments by persisting trading data to Redis and Database.
"""
import json
import redis
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sqlite3
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradeRecord:
    trade_id: str
    symbol: str
    action: str  # BUY/SELL
    quantity: int
    price: float
    timestamp: str
    pnl: float
    status: str
    strategy: str

@dataclass
class TradingSession:
    session_id: str
    start_time: str
    end_time: Optional[str]
    total_trades: int
    daily_pnl: float
    success_rate: float
    is_active: bool
    strategies_performance: Dict[str, Any]

class TradingDataPersistence:
    """Comprehensive data persistence for trading system"""
    
    def __init__(self, redis_url: str = None, db_path: str = "trading_data.db"):
        self.redis_client = None
        self.db_path = db_path
        self.current_session = None
        self.trades_cache = []
        
        # Initialize Redis if available
        try:
            if redis_url:
                self.redis_client = redis.from_url(redis_url)
            else:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            # Test Redis connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}")
            self.redis_client = None
        
        # Initialize SQLite database
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for persistent storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create trades table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        trade_id TEXT PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        action TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        price REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        pnl REAL NOT NULL,
                        status TEXT NOT NULL,
                        strategy TEXT NOT NULL
                    )
                ''')
                
                # Create sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trading_sessions (
                        session_id TEXT PRIMARY KEY,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        total_trades INTEGER NOT NULL,
                        daily_pnl REAL NOT NULL,
                        success_rate REAL NOT NULL,
                        is_active BOOLEAN NOT NULL,
                        strategies_performance TEXT
                    )
                ''')
                
                # Create performance metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        date TEXT PRIMARY KEY,
                        total_pnl REAL NOT NULL,
                        trade_count INTEGER NOT NULL,
                        win_rate REAL NOT NULL,
                        max_drawdown REAL NOT NULL,
                        sharpe_ratio REAL NOT NULL,
                        created_at TEXT NOT NULL
                    )
                ''')
                
                conn.commit()
                logger.info("✅ Database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    def save_trade(self, trade: TradeRecord):
        """Save individual trade to both Redis and Database"""
        try:
            # Save to Redis cache
            if self.redis_client:
                trade_key = f"trade:{trade.trade_id}"
                self.redis_client.hset(trade_key, mapping=asdict(trade))
                self.redis_client.expire(trade_key, 86400 * 7)  # 7 days expiry
                
                # Add to trades list
                self.redis_client.lpush("trades_list", trade.trade_id)
                logger.info(f"✅ Trade {trade.trade_id} saved to Redis")
            
            # Save to SQLite database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO trades 
                    (trade_id, symbol, action, quantity, price, timestamp, pnl, status, strategy)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.trade_id, trade.symbol, trade.action, trade.quantity,
                    trade.price, trade.timestamp, trade.pnl, trade.status, trade.strategy
                ))
                conn.commit()
                logger.info(f"✅ Trade {trade.trade_id} saved to database")
                
        except Exception as e:
            logger.error(f"❌ Failed to save trade {trade.trade_id}: {e}")
    
    def save_trading_session(self, session: TradingSession):
        """Save trading session data"""
        try:
            self.current_session = session
            
            # Save to Redis
            if self.redis_client:
                session_key = f"session:{session.session_id}"
                session_data = asdict(session)
                session_data['strategies_performance'] = json.dumps(session_data['strategies_performance'])
                
                self.redis_client.hset(session_key, mapping=session_data)
                self.redis_client.set("current_session", session.session_id)
                logger.info(f"✅ Session {session.session_id} saved to Redis")
            
            # Save to Database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO trading_sessions
                    (session_id, start_time, end_time, total_trades, daily_pnl, 
                     success_rate, is_active, strategies_performance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.session_id, session.start_time, session.end_time,
                    session.total_trades, session.daily_pnl, session.success_rate,
                    session.is_active, json.dumps(session.strategies_performance)
                ))
                conn.commit()
                logger.info(f"✅ Session {session.session_id} saved to database")
                
        except Exception as e:
            logger.error(f"❌ Failed to save session: {e}")
    
    def get_current_session(self) -> Optional[TradingSession]:
        """Retrieve current trading session data"""
        try:
            # Try Redis first
            if self.redis_client:
                session_id = self.redis_client.get("current_session")
                if session_id:
                    session_key = f"session:{session_id}"
                    session_data = self.redis_client.hgetall(session_key)
                    if session_data:
                        session_data['strategies_performance'] = json.loads(
                            session_data.get('strategies_performance', '{}')
                        )
                        return TradingSession(**session_data)
            
            # Fallback to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM trading_sessions 
                    WHERE is_active = 1 
                    ORDER BY start_time DESC 
                    LIMIT 1
                ''')
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    session_data = dict(zip(columns, row))
                    session_data['strategies_performance'] = json.loads(
                        session_data['strategies_performance']
                    )
                    return TradingSession(**session_data)
                    
        except Exception as e:
            logger.error(f"❌ Failed to get current session: {e}")
        
        return None
    
    def get_trades_for_session(self, session_id: str) -> List[TradeRecord]:
        """Get all trades for a specific session"""
        trades = []
        
        try:
            # Try database first (most reliable)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM trades 
                    WHERE timestamp >= (
                        SELECT start_time FROM trading_sessions 
                        WHERE session_id = ?
                    )
                    ORDER BY timestamp DESC
                ''', (session_id,))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                for row in rows:
                    trade_data = dict(zip(columns, row))
                    trades.append(TradeRecord(**trade_data))
                    
                logger.info(f"✅ Retrieved {len(trades)} trades from database")
                
        except Exception as e:
            logger.error(f"❌ Failed to get trades for session: {e}")
        
        return trades
    
    def create_emergency_backup(self) -> str:
        """Create complete backup of all trading data"""
        try:
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'backup_type': 'emergency_full_backup',
                'current_session': None,
                'all_trades': [],
                'all_sessions': [],
                'performance_metrics': []
            }
            
            # Get current session
            current_session = self.get_current_session()
            if current_session:
                backup_data['current_session'] = asdict(current_session)
            
            # Get all trades
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # All trades
                cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC')
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                backup_data['all_trades'] = [dict(zip(columns, row)) for row in rows]
                
                # All sessions
                cursor.execute('SELECT * FROM trading_sessions ORDER BY start_time DESC')
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                backup_data['all_sessions'] = [dict(zip(columns, row)) for row in rows]
            
            # Save backup file
            backup_filename = f"complete_trading_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_filename, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"✅ Complete backup created: {backup_filename}")
            return backup_filename
            
        except Exception as e:
            logger.error(f"❌ Emergency backup failed: {e}")
            return None
    
    def restore_from_backup(self, backup_file: str):
        """Restore trading data from backup file"""
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Restore trades
            for trade_data in backup_data.get('all_trades', []):
                trade = TradeRecord(**trade_data)
                self.save_trade(trade)
            
            # Restore sessions
            for session_data in backup_data.get('all_sessions', []):
                session_data['strategies_performance'] = json.loads(
                    session_data.get('strategies_performance', '{}')
                )
                session = TradingSession(**session_data)
                self.save_trading_session(session)
            
            logger.info(f"✅ Successfully restored from backup: {backup_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to restore from backup: {e}")
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get comprehensive recovery status"""
        status = {
            'redis_available': self.redis_client is not None,
            'database_available': os.path.exists(self.db_path),
            'current_session': None,
            'total_trades': 0,
            'total_sessions': 0,
            'last_backup': None
        }
        
        try:
            # Test Redis
            if self.redis_client:
                self.redis_client.ping()
                status['redis_status'] = 'connected'
            else:
                status['redis_status'] = 'unavailable'
            
            # Check database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM trades')
                status['total_trades'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM trading_sessions')
                status['total_sessions'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT * FROM trading_sessions WHERE is_active = 1 LIMIT 1')
                active_session = cursor.fetchone()
                if active_session:
                    columns = [description[0] for description in cursor.description]
                    status['current_session'] = dict(zip(columns, active_session))
            
            status['database_status'] = 'healthy'
            
        except Exception as e:
            status['database_status'] = f'error: {e}'
        
        return status

# Global persistence instance
trading_persistence = TradingDataPersistence()

# Convenience functions for easy integration
def save_trade_data(trade_id: str, symbol: str, action: str, quantity: int, 
                   price: float, pnl: float, status: str = "completed", 
                   strategy: str = "autonomous"):
    """Save trade data easily"""
    trade = TradeRecord(
        trade_id=trade_id,
        symbol=symbol,
        action=action,
        quantity=quantity,
        price=price,
        timestamp=datetime.now().isoformat(),
        pnl=pnl,
        status=status,
        strategy=strategy
    )
    trading_persistence.save_trade(trade)

def update_session_data(session_id: str, total_trades: int, daily_pnl: float, 
                       success_rate: float, is_active: bool = True):
    """Update current trading session"""
    session = TradingSession(
        session_id=session_id,
        start_time=datetime.now().isoformat(),
        end_time=None,
        total_trades=total_trades,
        daily_pnl=daily_pnl,
        success_rate=success_rate,
        is_active=is_active,
        strategies_performance={}
    )
    trading_persistence.save_trading_session(session)

def get_persistent_trading_data() -> Dict[str, Any]:
    """Get all persistent trading data for API responses"""
    try:
        current_session = trading_persistence.get_current_session()
        if not current_session:
            return {
                'total_trades': 0,
                'daily_pnl': 0.0,
                'success_rate': 0.0,
                'is_active': False
            }
        
        return {
            'total_trades': current_session.total_trades,
            'daily_pnl': current_session.daily_pnl,
            'success_rate': current_session.success_rate,
            'is_active': current_session.is_active,
            'session_id': current_session.session_id,
            'start_time': current_session.start_time
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get persistent data: {e}")
        return {
            'total_trades': 0,
            'daily_pnl': 0.0,
            'success_rate': 0.0,
            'is_active': False
        }

def create_emergency_backup():
    """Create emergency backup - easy to call"""
    return trading_persistence.create_emergency_backup()

def get_recovery_status():
    """Get recovery status - easy to call"""
    return trading_persistence.get_recovery_status()

if __name__ == "__main__":
    # Test the persistence system
    print("🧪 Testing Trading Data Persistence System")
    print("=" * 50)
    
    # Create test data
    test_trade = TradeRecord(
        trade_id="TEST_001",
        symbol="NIFTY",
        action="BUY",
        quantity=100,
        price=19500.0,
        timestamp=datetime.now().isoformat(),
        pnl=1500.0,
        status="completed",
        strategy="momentum"
    )
    
    # Save test trade
    trading_persistence.save_trade(test_trade)
    
    # Create test session
    test_session = TradingSession(
        session_id="SESSION_001",
        start_time=datetime.now().isoformat(),
        end_time=None,
        total_trades=1,
        daily_pnl=1500.0,
        success_rate=100.0,
        is_active=True,
        strategies_performance={"momentum": {"trades": 1, "pnl": 1500.0}}
    )
    
    # Save test session
    trading_persistence.save_trading_session(test_session)
    
    # Test recovery
    recovered_session = trading_persistence.get_current_session()
    print(f"✅ Recovered session: {recovered_session.session_id if recovered_session else 'None'}")
    
    # Test backup
    backup_file = trading_persistence.create_emergency_backup()
    print(f"✅ Backup created: {backup_file}")
    
    # Recovery status
    status = trading_persistence.get_recovery_status()
    print(f"✅ Recovery status: {status}")
    
    print("\n🎉 Persistence system test completed!") 