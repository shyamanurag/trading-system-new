#!/usr/bin/env python3
"""
Debug script to test orchestrator initialization step by step
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_orchestrator_init():
    """Debug orchestrator initialization step by step"""
    print("🔍 DEBUGGING ORCHESTRATOR INITIALIZATION")
    print("=========================================")
    
    try:
        print("1. Testing basic imports...")
        
        # Test EventBus import
        try:
            from src.events import EventBus
            print("✅ EventBus import successful")
            event_bus = EventBus()
            print("✅ EventBus creation successful")
        except Exception as e:
            print(f"❌ EventBus error: {e}")
            return
        
        # Test Redis import and connection
        try:
            import redis.asyncio as redis
            print("✅ Redis import successful")
            
            # Test Redis connection with DigitalOcean config
            redis_config = {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'password': os.getenv('REDIS_PASSWORD'),
                'username': os.getenv('REDIS_USERNAME', 'default'),
                'ssl': os.getenv('REDIS_SSL', 'false').lower() == 'true',
                'ssl_cert_reqs': None if os.getenv('REDIS_SSL', 'false').lower() == 'true' else 'required'
            }
            
            print(f"🔧 Testing Redis connection: {redis_config['host']}:{redis_config['port']} (SSL: {redis_config['ssl']})")
            
            redis_client = redis.Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                password=redis_config['password'],
                username=redis_config['username'],
                ssl=redis_config['ssl'],
                ssl_cert_reqs=redis_config['ssl_cert_reqs'],
                decode_responses=True
            )
            
            await redis_client.ping()
            print("✅ Redis connection successful")
        except Exception as e:
            print(f"❌ Redis error: {e}")
            return
        
        # Test PositionTracker import
        try:
            from src.core.position_tracker import PositionTracker
            print("✅ PositionTracker import successful")
            
            position_tracker = PositionTracker(
                event_bus=event_bus,
                redis_client=redis_client
            )
            print("✅ PositionTracker creation successful")
        except Exception as e:
            print(f"❌ PositionTracker error: {e}")
            return
        
        # Test orchestrator import
        try:
            from src.core.orchestrator import TradingOrchestrator
            print("✅ TradingOrchestrator import successful")
            
            orchestrator = TradingOrchestrator.get_instance()
            print("✅ TradingOrchestrator instance creation successful")
        except Exception as e:
            print(f"❌ TradingOrchestrator error: {e}")
            return
        
        # Test orchestrator initialization
        try:
            print("2. Testing orchestrator system initialization...")
            init_success = await orchestrator.initialize_system()
            print(f"Initialize system result: {init_success}")
            
            if init_success:
                print("✅ Orchestrator initialization successful!")
                
                # Test getting status
                status = await orchestrator.get_trading_status()
                print("✅ Trading status retrieved successfully")
                print(f"Status keys: {list(status.keys())}")
                
                if 'symbol_count' in status:
                    print("✅ symbol_count field present - orchestrator fully working!")
                else:
                    print("❌ symbol_count field missing - using fallback handler")
            else:
                print("❌ Orchestrator initialization failed")
                
        except Exception as e:
            print(f"❌ Orchestrator initialization error: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_orchestrator_init()) 