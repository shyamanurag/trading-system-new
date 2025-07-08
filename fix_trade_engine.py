#!/usr/bin/env python3
"""
Fix Trade Engine Component Issue
===============================
Diagnose and fix why trade engine component is False, blocking signal processing
"""

import requests
import json
import time

DEPLOYED_URL = "https://algoauto-9gx56.ondigitalocean.app"

def check_trade_engine_status():
    """Check current trade engine component status"""
    print("🔍 CHECKING TRADE ENGINE STATUS")
    print("=" * 40)
    
    try:
        # Check orchestrator debug
        response = requests.get(f"{DEPLOYED_URL}/api/v1/debug/orchestrator-debug", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            
            print(f"📊 Component Status:")
            for component, status in components.items():
                icon = "✅" if status else "❌"
                print(f"   {icon} {component}: {status}")
            
            trade_engine_status = components.get('trade_engine', False)
            print(f"\n🎯 TRADE ENGINE: {trade_engine_status}")
            
            if not trade_engine_status:
                print("🚨 PROBLEM IDENTIFIED: Trade engine component is False!")
                print("   This blocks signal processing → no trades")
                return False
            else:
                print("✅ Trade engine component is active")
                return True
                
        else:
            print(f"❌ Orchestrator debug failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking trade engine: {e}")
        return False

def force_initialize_system():
    """Force initialize system to fix trade engine"""
    print("\n🔧 FORCE INITIALIZING SYSTEM")
    print("=" * 30)
    
    try:
        response = requests.post(f"{DEPLOYED_URL}/api/v1/debug/force-initialize", timeout=15)
        
        print(f"Force Initialize Response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success', False):
                print("✅ Force initialization successful!")
                
                active_strategies = data.get('active_strategies', [])
                components_ready = data.get('components_ready', 0)
                
                print(f"   🎯 Active Strategies: {len(active_strategies)}")
                print(f"   📊 Components Ready: {components_ready}")
                
                return True
            else:
                error_msg = data.get('error', 'Unknown error')
                print(f"❌ Force initialization failed: {error_msg}")
                return False
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Force initialize error: {e}")
        return False

def verify_signal_processing():
    """Verify if signals are now being processed"""
    print("\n📡 VERIFYING SIGNAL PROCESSING")
    print("=" * 35)
    
    try:
        # Get recent signals
        response = requests.get(f"{DEPLOYED_URL}/api/v1/signals/recent", timeout=10)
        
        if response.status_code == 200:
            signals = response.json()
            
            if isinstance(signals, dict) and 'signals' in signals:
                signal_list = signals['signals']
                print(f"📊 Total Signals: {len(signal_list)}")
                
                if len(signal_list) > 0:
                    print("📡 Recent Signals:")
                    for signal in signal_list[-3:]:  # Last 3 signals
                        symbol = signal.get('symbol', 'UNKNOWN')
                        action = signal.get('action', 'UNKNOWN')
                        confidence = signal.get('confidence', 0)
                        strategy = signal.get('strategy', 'UNKNOWN')
                        
                        print(f"   📊 {symbol} {action} (Conf: {confidence:.1f}%) - {strategy}")
                else:
                    print("   ℹ️ No signals found")
            else:
                print("   ℹ️ No signals data available")
                
        # Check trading status
        response = requests.get(f"{DEPLOYED_URL}/api/v1/autonomous/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()['data']
            total_trades = data.get('total_trades', 0)
            
            print(f"\n💰 TRADE STATUS:")
            print(f"   Total Trades: {total_trades}")
            
            if total_trades > 0:
                print("✅ TRADES ARE BEING EXECUTED!")
                return True
            else:
                print("⏳ Still 0 trades - signals may not be converting")
                return False
                
    except Exception as e:
        print(f"❌ Error verifying signals: {e}")
        return False

def main():
    """Main diagnostic and fix function"""
    print("🚨 TRADE ENGINE DIAGNOSTIC & FIX")
    print("=" * 50)
    
    # Step 1: Check current status
    trade_engine_ok = check_trade_engine_status()
    
    # Step 2: Force initialize if needed
    if not trade_engine_ok:
        print("\n🔧 ATTEMPTING FIX...")
        initialize_ok = force_initialize_system()
        
        if initialize_ok:
            print("\n⏳ Waiting 10 seconds for system to stabilize...")
            time.sleep(10)
            
            # Re-check status
            trade_engine_ok = check_trade_engine_status()
        else:
            print("❌ Force initialization failed")
    
    # Step 3: Verify signal processing
    if trade_engine_ok:
        verify_signal_processing()
    
    print(f"\n🎯 SUMMARY:")
    if trade_engine_ok:
        print("✅ Trade engine component is now active")
        print("✅ Signals should be processing → trades")
        print("🔍 Monitor for actual trade generation")
    else:
        print("❌ Trade engine component still inactive")
        print("🚨 ROOT CAUSE: This blocks all signal processing")
        print("💡 Signals generated but never converted to trades")

if __name__ == "__main__":
    main() 