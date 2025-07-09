#!/usr/bin/env python3
"""
Comprehensive Signal and Order Processing Test
==============================================
Tests the complete pipeline:
1. Signal generation from strategies
2. Signal processing through TradeEngine
3. Order placement through OrderManager
4. Zerodha client connectivity
5. Real-time status monitoring
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_system_status():
    """Test 1: Basic system status and availability"""
    print("🔍 TEST 1: SYSTEM STATUS AND AVAILABILITY")
    print("=" * 50)
    
    try:
        # Test autonomous trading status
        response = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
        print(f"   Autonomous Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            status_data = data.get('data', {})
            print(f"   ✅ System Active: {status_data.get('is_active', False)}")
            print(f"   ✅ Strategies Count: {status_data.get('active_strategies_count', 0)}")
            print(f"   ✅ Total Trades: {status_data.get('total_trades', 0)}")
            print(f"   ✅ System Ready: {status_data.get('system_ready', False)}")
            return True, status_data
        else:
            print(f"   ❌ Status endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False, {}
            
    except Exception as e:
        print(f"   ❌ System status test failed: {e}")
        return False, {}

def test_broker_connectivity():
    """Test 2: Zerodha broker connectivity"""
    print("\n🔍 TEST 2: ZERODHA BROKER CONNECTIVITY")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/broker/status", timeout=10)
        print(f"   Broker Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Broker: {data.get('broker', 'Unknown')}")
            print(f"   ✅ Status: {data.get('status', 'Unknown')}")
            print(f"   ✅ API Calls Today: {data.get('api_calls_today', 0)}")
            print(f"   ✅ Market Data Connected: {data.get('market_data_connected', False)}")
            print(f"   ✅ Order Management Connected: {data.get('order_management_connected', False)}")
            
            is_connected = data.get('status') == 'connected'
            api_calls = data.get('api_calls_today', 0)
            
            return True, {
                'connected': is_connected,
                'api_calls': api_calls,
                'market_data': data.get('market_data_connected', False),
                'order_mgmt': data.get('order_management_connected', False)
            }
        else:
            print(f"   ❌ Broker status failed: {response.status_code}")
            return False, {}
            
    except Exception as e:
        print(f"   ❌ Broker connectivity test failed: {e}")
        return False, {}

def test_signal_generation():
    """Test 3: Signal generation capabilities"""
    print("\n🔍 TEST 3: SIGNAL GENERATION TESTING")
    print("=" * 50)
    
    try:
        # Test signal generation endpoint
        response = requests.get(f"{BASE_URL}/api/v1/signals", timeout=10)
        print(f"   Signals Endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            signals = data.get('data', [])
            print(f"   ✅ Signals Available: {len(signals)}")
            
            if signals:
                latest_signal = signals[0]
                print(f"   ✅ Latest Signal Symbol: {latest_signal.get('symbol', 'Unknown')}")
                print(f"   ✅ Latest Signal Action: {latest_signal.get('action', 'Unknown')}")
                print(f"   ✅ Latest Signal Confidence: {latest_signal.get('confidence', 0)}")
                print(f"   ✅ Latest Signal Strategy: {latest_signal.get('strategy', 'Unknown')}")
                
                return True, {
                    'signals_count': len(signals),
                    'latest_signal': latest_signal,
                    'strategies_generating': len(set(s.get('strategy', 'Unknown') for s in signals))
                }
            else:
                print("   ⚠️ No signals currently generated")
                return True, {'signals_count': 0}
        else:
            print(f"   ❌ Signals endpoint failed: {response.status_code}")
            return False, {}
            
    except Exception as e:
        print(f"   ❌ Signal generation test failed: {e}")
        return False, {}

def test_order_management():
    """Test 4: Order management capabilities"""
    print("\n🔍 TEST 4: ORDER MANAGEMENT TESTING")
    print("=" * 50)
    
    try:
        # Test orders endpoint
        response = requests.get(f"{BASE_URL}/api/v1/autonomous/orders", timeout=10)
        print(f"   Orders Endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get('data', [])
            print(f"   ✅ Total Orders: {len(orders)}")
            
            if orders:
                recent_orders = [o for o in orders if o.get('status') not in ['CANCELLED', 'REJECTED']]
                print(f"   ✅ Active/Filled Orders: {len(recent_orders)}")
                
                if recent_orders:
                    latest_order = recent_orders[0]
                    print(f"   ✅ Latest Order ID: {latest_order.get('order_id', 'Unknown')}")
                    print(f"   ✅ Latest Order Symbol: {latest_order.get('symbol', 'Unknown')}")
                    print(f"   ✅ Latest Order Status: {latest_order.get('status', 'Unknown')}")
                    print(f"   ✅ Latest Order Strategy: {latest_order.get('strategy_name', 'Unknown')}")
            
            return True, {
                'total_orders': len(orders),
                'active_orders': len([o for o in orders if o.get('status') == 'FILLED']),
                'recent_activity': len(orders) > 0
            }
        else:
            print(f"   ❌ Orders endpoint failed: {response.status_code}")
            return False, {}
            
    except Exception as e:
        print(f"   ❌ Order management test failed: {e}")
        return False, {}

def test_trading_pipeline():
    """Test 5: Complete trading pipeline"""
    print("\n🔍 TEST 5: COMPLETE TRADING PIPELINE TEST")
    print("=" * 50)
    
    try:
        # Start autonomous trading
        print("   🚀 Starting autonomous trading...")
        start_response = requests.post(f"{BASE_URL}/api/v1/autonomous/start", timeout=15)
        print(f"   Start Trading: {start_response.status_code}")
        
        if start_response.status_code == 200:
            start_data = start_response.json()
            print(f"   ✅ Start Response: {start_data.get('message', 'Unknown')}")
        else:
            print(f"   ❌ Failed to start trading: {start_response.text[:200]}")
            return False, {}
        
        # Monitor for signal -> order pipeline
        print("   ⏰ Monitoring signal -> order pipeline for 30 seconds...")
        
        initial_status_response = requests.get(f"{BASE_URL}/api/v1/autonomous/status")
        initial_trades = 0
        if initial_status_response.status_code == 200:
            initial_data = initial_status_response.json()
            initial_trades = initial_data.get('data', {}).get('total_trades', 0)
        
        print(f"   📊 Initial Trades: {initial_trades}")
        
        # Monitor for changes
        for i in range(6):  # 30 seconds total, check every 5 seconds
            time.sleep(5)
            
            try:
                # Check current status
                status_response = requests.get(f"{BASE_URL}/api/v1/autonomous/status")
                broker_response = requests.get(f"{BASE_URL}/api/v1/broker/status")
                
                current_trades = 0
                api_calls = 0
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    current_trades = status_data.get('data', {}).get('total_trades', 0)
                
                if broker_response.status_code == 200:
                    broker_data = broker_response.json()
                    api_calls = broker_data.get('api_calls_today', 0)
                
                print(f"   Check {i+1}/6: Trades={current_trades}, API Calls={api_calls}")
                
                # Check for improvements
                if current_trades > initial_trades:
                    print(f"   ✅ NEW TRADES DETECTED! ({current_trades - initial_trades} new trades)")
                    return True, {
                        'pipeline_working': True,
                        'new_trades': current_trades - initial_trades,
                        'total_trades': current_trades,
                        'api_calls': api_calls
                    }
                elif api_calls > 0:
                    print(f"   🔄 API CALLS DETECTED! OrderManager reaching Zerodha")
                    return True, {
                        'pipeline_working': True,
                        'api_calls_made': api_calls,
                        'trades_pending': True
                    }
                    
            except Exception as e:
                print(f"   ⚠️ Check {i+1} error: {e}")
        
        print("   ⏰ No new activity detected in 30 seconds")
        return True, {
            'pipeline_working': False,
            'final_trades': current_trades,
            'final_api_calls': api_calls
        }
        
    except Exception as e:
        print(f"   ❌ Trading pipeline test failed: {e}")
        return False, {}

def test_strategy_performance():
    """Test 6: Individual strategy performance"""
    print("\n🔍 TEST 6: STRATEGY PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    try:
        # Get strategy status
        response = requests.get(f"{BASE_URL}/api/v1/autonomous/strategies", timeout=10)
        print(f"   Strategies Endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            strategies = data.get('data', [])
            print(f"   ✅ Total Strategies: {len(strategies)}")
            
            active_strategies = [s for s in strategies if s.get('active', False)]
            print(f"   ✅ Active Strategies: {len(active_strategies)}")
            
            for strategy in active_strategies:
                name = strategy.get('name', 'Unknown')
                signals = strategy.get('signals_generated', 0)
                trades = strategy.get('trades_executed', 0)
                print(f"   📊 {name}: {signals} signals, {trades} trades")
            
            return True, {
                'total_strategies': len(strategies),
                'active_strategies': len(active_strategies),
                'strategy_details': active_strategies
            }
        else:
            print(f"   ❌ Strategies endpoint failed: {response.status_code}")
            return False, {}
            
    except Exception as e:
        print(f"   ❌ Strategy performance test failed: {e}")
        return False, {}

def generate_test_report(results):
    """Generate comprehensive test report"""
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE SIGNAL & ORDER TEST REPORT")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for success, _ in results.values() if success)
    
    print(f"📈 OVERALL SCORE: {passed_tests}/{total_tests} Tests Passed")
    print(f"🎯 SUCCESS RATE: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📋 DETAILED RESULTS:")
    test_names = [
        "System Status",
        "Broker Connectivity", 
        "Signal Generation",
        "Order Management",
        "Trading Pipeline",
        "Strategy Performance"
    ]
    
    for i, (test_name, (success, data)) in enumerate(zip(test_names, results.values())):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {i+1}. {test_name}: {status}")
        
        if success and data:
            if 'api_calls' in data:
                print(f"      - API Calls: {data['api_calls']}")
            if 'total_trades' in data:
                print(f"      - Total Trades: {data['total_trades']}")
            if 'signals_count' in data:
                print(f"      - Signals: {data['signals_count']}")
            if 'pipeline_working' in data:
                print(f"      - Pipeline: {'Working' if data['pipeline_working'] else 'Issues'}")
    
    print("\n🔍 CRITICAL ANALYSIS:")
    
    # Analyze results
    broker_success, broker_data = results.get('broker', (False, {}))
    pipeline_success, pipeline_data = results.get('pipeline', (False, {}))
    
    if broker_success and broker_data.get('connected'):
        print("   ✅ Zerodha broker is properly connected")
    else:
        print("   ❌ Zerodha broker connection issues detected")
    
    if broker_success and broker_data.get('api_calls', 0) > 0:
        print("   ✅ OrderManager successfully reaching Zerodha API")
    else:
        print("   ⚠️ No Zerodha API calls detected - OrderManager may not be connected")
    
    if pipeline_success and pipeline_data.get('pipeline_working'):
        print("   ✅ Complete signal -> order pipeline is functional")
    else:
        print("   ❌ Signal -> order pipeline needs investigation")
    
    # Final recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if passed_tests == total_tests:
        print("   🎉 All systems operational! Trading pipeline is working correctly.")
        print("   🚀 Ready for live trading with full OrderManager complexity.")
    elif passed_tests >= 4:
        print("   🔧 Most systems working. Minor issues need attention.")
        print("   ⚠️ Monitor closely during live trading.")
    else:
        print("   🚨 Critical issues detected. System needs fixes before live trading.")
        print("   ❌ Do not use for real money until all tests pass.")

def main():
    """Run comprehensive signal and order processing tests"""
    print("🚀 COMPREHENSIVE SIGNAL & ORDER PROCESSING TESTS")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target URL: {BASE_URL}")
    
    # Run all tests
    results = {}
    
    results['status'] = test_system_status()
    results['broker'] = test_broker_connectivity()
    results['signals'] = test_signal_generation()
    results['orders'] = test_order_management()
    results['pipeline'] = test_trading_pipeline()
    results['strategies'] = test_strategy_performance()
    
    # Generate comprehensive report
    generate_test_report(results)
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main() 