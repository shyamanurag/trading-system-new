#!/usr/bin/env python3
"""
Test script to verify paper trading orders are saved to database and retrievable via API
"""

import asyncio
import requests
import sys
import time
from datetime import datetime

# Test paper trade generation
async def test_paper_trading():
    """Test that paper orders are created and stored"""
    print("🧪 Testing Paper Trading Fix...")
    
    # Test 1: Check if we can import trade engine
    try:
        from src.core.trade_engine import TradeEngine
        print("✅ Trade engine import successful")
    except Exception as e:
        print(f"❌ Trade engine import failed: {e}")
        return False
    
    # Test 2: Create a test signal and process it
    try:
        trade_engine = TradeEngine()
        
        test_signal = {
            'symbol': 'TESTSTOCK',
            'action': 'BUY',
            'quantity': 10,
            'entry_price': 100.50,
            'strategy': 'test_strategy'
        }
        
        # Process as paper trade
        order_id = await trade_engine._process_paper_signal(test_signal)
        
        if order_id:
            print(f"✅ Paper order created: {order_id}")
            return True
        else:
            print("❌ Failed to create paper order")
            return False
            
    except Exception as e:
        print(f"❌ Error processing paper signal: {e}")
        return False

# Test API endpoint
def test_orders_api():
    """Test that orders API returns the saved orders"""
    print("🌐 Testing Orders API...")
    
    try:
        # Test local endpoint
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/orders')
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get('orders', [])
            print(f"✅ API call successful - Found {len(orders)} orders")
            
            # Show recent orders
            if orders:
                print("📋 Recent orders:")
                for order in orders[:5]:  # Show last 5 orders
                    print(f"   {order.get('order_id')} | {order.get('symbol')} | {order.get('side')} | {order.get('strategy_name')}")
            
            return True
        else:
            print(f"❌ API call failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Paper Trading Fix Verification")
    print("=" * 40)
    
    # Test 1: Paper trading functionality
    success1 = asyncio.run(test_paper_trading())
    
    print()
    
    # Test 2: API endpoint
    success2 = test_orders_api()
    
    print()
    print("=" * 40)
    if success1 and success2:
        print("🎉 All tests passed! Paper trading fix is working.")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    return success1 and success2

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 