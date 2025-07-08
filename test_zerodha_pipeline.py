#!/usr/bin/env python3
"""
Comprehensive Zerodha Pipeline Test
Tests the complete order execution pipeline from signals to Zerodha API
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_zerodha_credentials():
    """Test Zerodha credentials and environment setup"""
    print("🔍 Testing Zerodha Credentials...")
    
    # Check environment variables
    required_vars = ['ZERODHA_API_KEY', 'ZERODHA_API_SECRET', 'ZERODHA_USER_ID']
    optional_vars = ['ZERODHA_ACCESS_TOKEN', 'ZERODHA_PIN']
    
    credentials = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            credentials[var] = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {credentials[var]}")
        else:
            missing_vars.append(var)
            print(f"❌ {var}: NOT SET")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            credentials[var] = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {credentials[var]}")
        else:
            print(f"⚠️  {var}: NOT SET (optional)")
    
    if missing_vars:
        print(f"❌ Missing required variables: {missing_vars}")
        return False
    
    print("✅ All required Zerodha credentials are set")
    return True

async def test_zerodha_connection():
    """Test Zerodha connection and authentication"""
    print("\n🔍 Testing Zerodha Connection...")
    
    try:
        # Test the production Zerodha implementation
        from src.core.zerodha import ZerodhaIntegration
        
        config = {
            'api_key': os.getenv('ZERODHA_API_KEY'),
            'api_secret': os.getenv('ZERODHA_API_SECRET'),
            'user_id': os.getenv('ZERODHA_USER_ID'),
            'access_token': os.getenv('ZERODHA_ACCESS_TOKEN'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379')
        }
        
        zerodha = ZerodhaIntegration(config)
        
        # Test initialization
        await zerodha.initialize()
        
        # Test connection status
        is_connected = await zerodha.is_connected()
        print(f"✅ Connection Status: {'Connected' if is_connected else 'Disconnected'}")
        
        # Test authentication if connected
        if is_connected:
            try:
                # Test by getting margins (this requires valid authentication)
                margins = await zerodha.get_margins()
                print(f"✅ Authentication Status: Valid")
                print(f"   Available Cash: ₹{margins.get('available_cash', 0):,.2f}")
                print(f"   Used Margin: ₹{margins.get('used_margin', 0):,.2f}")
                print(f"   Available Margin: ₹{margins.get('available_margin', 0):,.2f}")
                
                # Test getting orders
                orders = await zerodha.get_orders()
                print(f"✅ Orders Today: {len(orders)} orders")
                
                # Test getting positions
                positions = await zerodha.get_positions()
                print(f"✅ Positions: {len(positions)} positions")
                
                return True
                
            except Exception as e:
                print(f"❌ Authentication Error: {e}")
                return False
        else:
            print("❌ Not connected to Zerodha")
            return False
            
    except Exception as e:
        print(f"❌ Connection Test Failed: {e}")
        return False

async def test_orchestrator_zerodha_integration():
    """Test Zerodha integration in orchestrator"""
    print("\n🔍 Testing Orchestrator Zerodha Integration...")
    
    try:
        from src.core.orchestrator import TradingOrchestrator
        
        # Create orchestrator instance
        orchestrator = TradingOrchestrator()
        
        # Initialize orchestrator
        await orchestrator.initialize()
        
        # Check component status
        components = orchestrator.components
        print(f"✅ Orchestrator Components Status:")
        for component, status in components.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {component}: {status}")
        
        # Check if Zerodha is available
        zerodha_status = components.get('zerodha', False)
        print(f"\n🔍 Zerodha Component Status: {zerodha_status}")
        
        # Test the bypass logic (the fix mentioned in memory)
        if hasattr(orchestrator, 'zerodha') and orchestrator.zerodha:
            print("✅ Zerodha client available via orchestrator")
        else:
            print("⚠️  Zerodha client not available via orchestrator - bypass logic will be used")
        
        return orchestrator
        
    except Exception as e:
        print(f"❌ Orchestrator Integration Error: {e}")
        return None

async def test_signal_processing():
    """Test signal processing through Zerodha pipeline"""
    print("\n🔍 Testing Signal Processing Pipeline...")
    
    try:
        from src.core.orchestrator import TradeEngine
        
        # Create trade engine
        trade_engine = TradeEngine()
        await trade_engine.initialize()
        
        # Create test signal
        test_signal = {
            'symbol': 'NIFTY25JAN26000PE',
            'action': 'BUY',
            'confidence': 0.85,
            'strategy': 'TEST_STRATEGY',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Test Signal Created: {test_signal}")
        
        # Process signal (this will test the bypass logic)
        await trade_engine.process_signals([test_signal])
        
        # Check signal queue
        signal_queue = trade_engine.signal_queue
        print(f"✅ Signals in Queue: {len(signal_queue)}")
        
        for i, queued_signal in enumerate(signal_queue):
            print(f"   Signal {i+1}:")
            print(f"     Symbol: {queued_signal['signal']['symbol']}")
            print(f"     Action: {queued_signal['signal']['action']}")
            print(f"     Processed: {queued_signal['processed']}")
            print(f"     Status: {queued_signal.get('status', 'UNKNOWN')}")
            if 'order_id' in queued_signal:
                print(f"     Order ID: {queued_signal['order_id']}")
        
        return len(signal_queue) > 0
        
    except Exception as e:
        print(f"❌ Signal Processing Error: {e}")
        return False

async def test_redis_connection():
    """Test Redis connection for token storage"""
    print("\n🔍 Testing Redis Connection...")
    
    try:
        import redis.asyncio as redis
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = redis.from_url(redis_url)
        
        # Test connection
        await redis_client.ping()
        print(f"✅ Redis Connected: {redis_url}")
        
        # Check for stored tokens
        user_id = os.getenv('ZERODHA_USER_ID', '')
        if user_id:
            token_key = f"zerodha:token:{user_id}"
            stored_token = await redis_client.get(token_key)
            
            if stored_token:
                print(f"✅ Stored Token Found: {stored_token[:10]}...")
            else:
                print("⚠️  No stored token found")
        
        await redis_client.close()
        return True
        
    except Exception as e:
        print(f"❌ Redis Connection Error: {e}")
        return False

async def generate_pipeline_report():
    """Generate comprehensive pipeline report"""
    print("\n📊 Generating Pipeline Report...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # Run all tests
    tests = [
        ('credentials', test_zerodha_credentials),
        ('redis_connection', test_redis_connection),
        ('zerodha_connection', test_zerodha_connection),
        ('orchestrator_integration', test_orchestrator_zerodha_integration),
        ('signal_processing', test_signal_processing)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            report['tests'][test_name] = {
                'status': 'PASS' if result else 'FAIL',
                'result': result
            }
        except Exception as e:
            report['tests'][test_name] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    # Generate summary
    passed = sum(1 for test in report['tests'].values() if test['status'] == 'PASS')
    total = len(report['tests'])
    
    print(f"\n📈 Pipeline Report Summary:")
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")
    
    # Save report
    with open('zerodha_pipeline_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report saved to: zerodha_pipeline_report.json")
    
    return report

async def main():
    """Main test runner"""
    print("🚀 Zerodha Pipeline Comprehensive Test")
    print("=" * 50)
    
    # Generate comprehensive report
    report = await generate_pipeline_report()
    
    # Print final status
    print("\n" + "=" * 50)
    if all(test['status'] == 'PASS' for test in report['tests'].values()):
        print("🎉 ALL TESTS PASSED - Zerodha Pipeline is Ready!")
    else:
        print("⚠️  Some tests failed - Review report for details")
    
    return report

if __name__ == "__main__":
    asyncio.run(main()) 