#!/usr/bin/env python3
"""
OrderManager Debug Test - Identify Specific Failing Component
============================================================
Test each OrderManager dependency individually to find the exact failure point
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add src directory to path
src_path = str(Path(__file__).parent / 'src')
if src_path not in sys.path:
    sys.path.append(src_path)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_order_manager_dependencies():
    """Test each OrderManager dependency individually"""
    
    print("🔍 TESTING ORDERMANAGER DEPENDENCIES INDIVIDUALLY")
    print("=" * 60)
    
    # Create the same config used by orchestrator
    config = {
        'redis': {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
            'password': os.getenv('REDIS_PASSWORD'),
            'ssl': os.getenv('REDIS_SSL', 'false').lower() == 'true'
        },
        'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
        'database': {
            'url': os.getenv('DATABASE_URL', 'sqlite:///trading.db')
        },
        'trading': {
            'max_daily_loss': 100000,
            'max_position_size': 1000000,
            'risk_per_trade': 0.02
        },
        'notifications': {
            'enabled': True,
            'email_alerts': False,
            'sms_alerts': False
        }
    }
    
    print(f"📋 Config: Redis={config['redis']['host']}:{config['redis']['port']}")
    print(f"📋 Config: Database={config['database']['url']}")
    
    # Test 1: Redis Connection
    print(f"\n1. TESTING REDIS CONNECTION")
    try:
        import redis.asyncio as redis
        redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            db=config['redis']['db']
        )
        await redis_client.ping()
        print("✅ Redis connection: SUCCESS")
    except Exception as e:
        print(f"❌ Redis connection: FAILED - {e}")
    
    # Test 2: UserTracker
    print(f"\n2. TESTING USERTRACKER")
    try:
        from src.core.user_tracker import UserTracker
        user_tracker = UserTracker(config)
        print("✅ UserTracker initialization: SUCCESS")
    except Exception as e:
        print(f"❌ UserTracker initialization: FAILED - {e}")
    
    # Test 3: RiskManager
    print(f"\n3. TESTING RISKMANAGER") 
    try:
        from src.core.risk_manager import RiskManager
        from src.core.position_tracker import ProductionPositionTracker
        from src.events import EventBus
        
        # Create required dependencies
        event_bus = EventBus()
        position_tracker = ProductionPositionTracker()
        
        risk_manager = RiskManager(config, position_tracker, event_bus)
        print("✅ RiskManager initialization: SUCCESS")
    except Exception as e:
        print(f"❌ RiskManager initialization: FAILED - {e}")
        
    # Test 3b: Try simpler RiskManager if the above fails
    try:
        from src.core.risk_manager import RiskManager
        # Try with None parameters (fallback)
        risk_manager = RiskManager(config, None, None)
        print("✅ RiskManager (fallback) initialization: SUCCESS")
    except Exception as e:
        print(f"❌ RiskManager (fallback) initialization: FAILED - {e}")
    
    # Test 4: TradeAllocator
    print(f"\n4. TESTING TRADEALLOCATOR")
    try:
        from src.core.trade_allocator import TradeAllocator
        trade_allocator = TradeAllocator(config)
        print("✅ TradeAllocator initialization: SUCCESS")
    except Exception as e:
        print(f"❌ TradeAllocator initialization: FAILED - {e}")
    
    # Test 5: SystemEvolution
    print(f"\n5. TESTING SYSTEMEVOLUTION")
    try:
        from src.core.system_evolution import SystemEvolution
        system_evolution = SystemEvolution(config)
        print("✅ SystemEvolution initialization: SUCCESS")
    except Exception as e:
        print(f"❌ SystemEvolution initialization: FAILED - {e}")
    
    # Test 6: CapitalManager
    print(f"\n6. TESTING CAPITALMANAGER")
    try:
        from src.core.capital_manager import CapitalManager
        capital_manager = CapitalManager(config)
        print("✅ CapitalManager initialization: SUCCESS")
    except Exception as e:
        print(f"❌ CapitalManager initialization: FAILED - {e}")
    
    # Test 7: NotificationManager
    print(f"\n7. TESTING NOTIFICATIONMANAGER")
    try:
        from src.core.notification_manager import NotificationManager
        notification_manager = NotificationManager(config)
        print("✅ NotificationManager initialization: SUCCESS")
    except Exception as e:
        print(f"❌ NotificationManager initialization: FAILED - {e}")
    
    # Test 8: Complete OrderManager
    print(f"\n8. TESTING COMPLETE ORDERMANAGER")
    try:
        from src.core.order_manager import OrderManager
        order_manager = OrderManager(config)
        print("✅ OrderManager initialization: SUCCESS")
        
        # Test a simple method
        print("\n9. TESTING ORDERMANAGER METHOD")
        test_signal = {
            'symbol': 'NIFTY',
            'action': 'BUY',
            'entry_price': 24500,
            'stop_loss': 24400,
            'target': 24600,
            'confidence': 0.8,
            'strategy': 'test_strategy'
        }
        
        try:
            # Test the method that's failing
            placed_orders = await order_manager.place_strategy_order('test_strategy', test_signal)
            print(f"✅ place_strategy_order: SUCCESS - {len(placed_orders) if placed_orders else 0} orders")
        except Exception as e:
            print(f"❌ place_strategy_order: FAILED - {e}")
            
    except Exception as e:
        print(f"❌ OrderManager initialization: FAILED - {e}")
    
    print("\n" + "=" * 60)
    print("🎯 ORDERMANAGER DEPENDENCY TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_order_manager_dependencies()) 