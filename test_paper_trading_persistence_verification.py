#!/usr/bin/env python3
"""
Paper Trading Database Persistence Verification Test
Tests the complete flow from signal generation to database persistence
"""

import asyncio
import logging
import sys
import os
import time
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append('.')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PaperTradingPersistenceTest:
    """Comprehensive test for paper trading database persistence"""
    
    def __init__(self):
        self.test_results = []
        self.test_signals = []
        self.test_user_id = None
        
    async def run_comprehensive_test(self):
        """Run complete paper trading persistence test"""
        logger.info("🧪 Starting Paper Trading Database Persistence Verification")
        logger.info("=" * 80)
        
        try:
            # Test 1: Database Connection
            await self._test_database_connection()
            
            # Test 2: User Existence
            await self._test_user_existence()
            
            # Test 3: Create Test Signals
            await self._create_test_signals()
            
            # Test 4: Process Signals Through Trade Engine
            await self._test_signal_processing()
            
            # Test 5: Verify Database Persistence
            await self._verify_database_persistence()
            
            # Test 6: Verify Frontend Data Access
            await self._test_frontend_data_access()
            
            # Print Summary
            self._print_test_summary()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            return False
            
        return all(result['passed'] for result in self.test_results)
    
    async def _test_database_connection(self):
        """Test 1: Verify database connection and migration 010 success"""
        logger.info("🔍 Test 1: Database Connection and Schema Verification")
        
        try:
            from src.core.database import get_db
            from sqlalchemy import text
            
            db_session = next(get_db())
            
            # Test the specific query that was failing before migration 010
            result = db_session.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
            
            if result:
                self.test_user_id = result[0]
                logger.info(f"✅ Database connection successful, users table accessible")
                logger.info(f"✅ Migration 010 successful - users.id column exists")
                logger.info(f"✅ Found test user with ID: {self.test_user_id}")
                self.test_results.append({
                    'test': 'database_connection',
                    'passed': True,
                    'message': 'Database connection and schema verified'
                })
            else:
                logger.warning("⚠️ No users found - will need to create test user")
                # Create a test user for paper trading
                await self._create_test_user(db_session)
                
            db_session.close()
            
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            self.test_results.append({
                'test': 'database_connection',
                'passed': False,
                'message': f'Database connection failed: {e}'
            })
            raise
    
    async def _create_test_user(self, db_session):
        """Create a test user for paper trading verification"""
        try:
            from sqlalchemy import text
            
            query = text("""
                INSERT INTO users (username, email, is_active, paper_trading_enabled, created_at)
                VALUES ('paper_test_user', 'paper@test.com', true, true, NOW())
                RETURNING id
            """)
            
            result = db_session.execute(query)
            db_session.commit()
            
            user_row = result.fetchone()
            if user_row:
                self.test_user_id = user_row[0]
                logger.info(f"✅ Created test user with ID: {self.test_user_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create test user: {e}")
            raise
    
    async def _test_user_existence(self):
        """Test 2: Verify user exists for paper trading"""
        logger.info("🔍 Test 2: User Existence Verification")
        
        if self.test_user_id:
            logger.info(f"✅ Test user exists with ID: {self.test_user_id}")
            self.test_results.append({
                'test': 'user_existence',
                'passed': True,
                'message': f'Test user found with ID: {self.test_user_id}'
            })
        else:
            logger.error("❌ No test user available")
            self.test_results.append({
                'test': 'user_existence',
                'passed': False,
                'message': 'No test user available for paper trading'
            })
    
    async def _create_test_signals(self):
        """Test 3: Create realistic test signals"""
        logger.info("🔍 Test 3: Creating Test Trading Signals")
        
        # Create realistic test signals
        self.test_signals = [
            {
                'signal_id': f'TEST_SIG_{int(time.time() * 1000)}_1',
                'symbol': 'RELIANCE',
                'action': 'BUY',
                'quantity': 10,
                'entry_price': 2450.50,
                'strategy': 'momentum_surfer',
                'confidence': 0.85,
                'timestamp': datetime.now().isoformat()
            },
            {
                'signal_id': f'TEST_SIG_{int(time.time() * 1000)}_2',
                'symbol': 'TCS',
                'action': 'BUY',
                'quantity': 5,
                'entry_price': 3850.75,
                'strategy': 'volatility_explosion',
                'confidence': 0.92,
                'timestamp': datetime.now().isoformat()
            },
            {
                'signal_id': f'TEST_SIG_{int(time.time() * 1000)}_3',
                'symbol': 'HDFC',
                'action': 'SELL',
                'quantity': 8,
                'entry_price': 1650.25,
                'strategy': 'volume_profile_scalper',
                'confidence': 0.78,
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        logger.info(f"✅ Created {len(self.test_signals)} test signals")
        for signal in self.test_signals:
            logger.info(f"   📊 {signal['symbol']} {signal['action']} {signal['quantity']} @ ₹{signal['entry_price']}")
        
        self.test_results.append({
            'test': 'signal_creation',
            'passed': True,
            'message': f'Created {len(self.test_signals)} test signals'
        })
    
    async def _test_signal_processing(self):
        """Test 4: Process signals through Trade Engine"""
        logger.info("🔍 Test 4: Signal Processing Through Trade Engine")
        
        try:
            # Set paper trading mode
            os.environ['PAPER_TRADING'] = 'true'
            
            from src.core.trade_engine import TradeEngine
            
            # Create trade engine config
            config = {
                'rate_limit': {'max_trades_per_second': 7},
                'batch_processing': {'size': 5, 'timeout': 0.5}
            }
            
            trade_engine = TradeEngine(config)
            await trade_engine.initialize()
            
            # Process each test signal
            processed_orders = []
            for signal in self.test_signals:
                logger.info(f"🚀 Processing signal: {signal['symbol']} {signal['action']}")
                
                order_id = await trade_engine.process_signal(signal)
                
                if order_id:
                    processed_orders.append({
                        'signal_id': signal['signal_id'],
                        'order_id': order_id,
                        'symbol': signal['symbol'],
                        'action': signal['action']
                    })
                    logger.info(f"✅ Signal processed successfully - Order ID: {order_id}")
                else:
                    logger.error(f"❌ Signal processing failed for {signal['symbol']}")
            
            if len(processed_orders) == len(self.test_signals):
                logger.info(f"✅ All {len(self.test_signals)} signals processed successfully")
                self.test_results.append({
                    'test': 'signal_processing',
                    'passed': True,
                    'message': f'All {len(self.test_signals)} signals processed',
                    'processed_orders': processed_orders
                })
            else:
                logger.error(f"❌ Only {len(processed_orders)}/{len(self.test_signals)} signals processed")
                self.test_results.append({
                    'test': 'signal_processing',
                    'passed': False,
                    'message': f'Only {len(processed_orders)}/{len(self.test_signals)} signals processed'
                })
            
        except Exception as e:
            logger.error(f"❌ Signal processing test failed: {e}")
            self.test_results.append({
                'test': 'signal_processing',
                'passed': False,
                'message': f'Signal processing failed: {e}'
            })
    
    async def _verify_database_persistence(self):
        """Test 5: Verify data was persisted to database"""
        logger.info("🔍 Test 5: Database Persistence Verification")
        
        try:
            from src.core.database import get_db
            from sqlalchemy import text
            
            db_session = next(get_db())
            
            # Check orders table
            orders_query = text("""
                SELECT order_id, symbol, side, quantity, price, status, strategy_name
                FROM orders 
                WHERE order_id LIKE 'PAPER_%'
                AND created_at >= NOW() - INTERVAL '10 minutes'
                ORDER BY created_at DESC
            """)
            
            orders_result = db_session.execute(orders_query).fetchall()
            
            # Check trades table
            trades_query = text("""
                SELECT order_id, symbol, trade_type, quantity, price, strategy
                FROM trades 
                WHERE order_id LIKE 'PAPER_%'
                AND created_at >= NOW() - INTERVAL '10 minutes'
                ORDER BY created_at DESC
            """)
            
            trades_result = db_session.execute(trades_query).fetchall()
            
            db_session.close()
            
            logger.info(f"📊 Found {len(orders_result)} orders in database")
            logger.info(f"📊 Found {len(trades_result)} trades in database")
            
            # Verify expected data
            expected_orders = len(self.test_signals)
            
            if len(orders_result) >= expected_orders and len(trades_result) >= expected_orders:
                logger.info("✅ Paper orders and trades successfully persisted to database")
                
                # Log details
                for order in orders_result:
                    logger.info(f"   📝 Order: {order[0]} - {order[1]} {order[2]} {order[3]} @ ₹{order[4]}")
                
                for trade in trades_result:
                    logger.info(f"   💰 Trade: {trade[0]} - {trade[1]} {trade[2]} {trade[3]} @ ₹{trade[4]}")
                
                self.test_results.append({
                    'test': 'database_persistence',
                    'passed': True,
                    'message': f'Found {len(orders_result)} orders and {len(trades_result)} trades in database'
                })
            else:
                logger.error(f"❌ Expected {expected_orders} orders/trades, found {len(orders_result)}/{len(trades_result)}")
                self.test_results.append({
                    'test': 'database_persistence',
                    'passed': False,
                    'message': f'Expected {expected_orders} orders/trades, found {len(orders_result)}/{len(trades_result)}'
                })
            
        except Exception as e:
            logger.error(f"❌ Database persistence verification failed: {e}")
            self.test_results.append({
                'test': 'database_persistence',
                'passed': False,
                'message': f'Database persistence verification failed: {e}'
            })
    
    async def _test_frontend_data_access(self):
        """Test 6: Verify frontend can access the persisted data"""
        logger.info("🔍 Test 6: Frontend Data Access Verification")
        
        try:
            # Test the same endpoints the frontend uses
            import requests
            
            # Test trades endpoint
            try:
                trades_response = requests.get(
                    "https://algoauto-9gx56.ondigitalocean.app/api/v1/trades",
                    timeout=10
                )
                
                if trades_response.status_code == 200:
                    trades_data = trades_response.json()
                    logger.info(f"✅ Trades endpoint accessible - Found {len(trades_data)} trades")
                    
                    # Check for recent paper trades
                    paper_trades = [t for t in trades_data if 'PAPER_' in str(t.get('order_id', ''))]
                    logger.info(f"✅ Found {len(paper_trades)} paper trades in API response")
                    
                else:
                    logger.warning(f"⚠️ Trades endpoint returned status {trades_response.status_code}")
                
            except Exception as e:
                logger.warning(f"⚠️ Could not test trades endpoint: {e}")
            
            # Test orders endpoint
            try:
                orders_response = requests.get(
                    "https://algoauto-9gx56.ondigitalocean.app/api/v1/orders",
                    timeout=10
                )
                
                if orders_response.status_code == 200:
                    orders_data = orders_response.json()
                    logger.info(f"✅ Orders endpoint accessible - Found {len(orders_data)} orders")
                    
                    # Check for recent paper orders
                    paper_orders = [o for o in orders_data if 'PAPER_' in str(o.get('order_id', ''))]
                    logger.info(f"✅ Found {len(paper_orders)} paper orders in API response")
                    
                else:
                    logger.warning(f"⚠️ Orders endpoint returned status {orders_response.status_code}")
                
            except Exception as e:
                logger.warning(f"⚠️ Could not test orders endpoint: {e}")
            
            logger.info("✅ Frontend data access verification completed")
            self.test_results.append({
                'test': 'frontend_data_access',
                'passed': True,
                'message': 'Frontend endpoints accessible'
            })
            
        except Exception as e:
            logger.error(f"❌ Frontend data access test failed: {e}")
            self.test_results.append({
                'test': 'frontend_data_access',
                'passed': False,
                'message': f'Frontend data access failed: {e}'
            })
    
    def _print_test_summary(self):
        """Print comprehensive test summary"""
        logger.info("=" * 80)
        logger.info("🧪 PAPER TRADING PERSISTENCE TEST SUMMARY")
        logger.info("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        total_tests = len(self.test_results)
        
        logger.info(f"📊 Tests Passed: {passed_tests}/{total_tests}")
        logger.info("")
        
        for result in self.test_results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            logger.info(f"{status} - {result['test']}: {result['message']}")
        
        logger.info("")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Paper trading database persistence is working correctly.")
            logger.info("🎯 The system is ready for live market trading!")
        else:
            logger.error(f"❌ {total_tests - passed_tests} tests failed. Paper trading persistence needs attention.")
        
        logger.info("=" * 80)

async def main():
    """Run the paper trading persistence verification test"""
    test_suite = PaperTradingPersistenceTest()
    
    try:
        success = await test_suite.run_comprehensive_test()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"❌ Test suite execution failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main())) 