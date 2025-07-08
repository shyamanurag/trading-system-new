#!/usr/bin/env python3
"""
Simple Trading System Starter - MINIMAL EFFECTIVE SOLUTION
==========================================================
Starts autonomous trading using simple trader instead of complex orchestrator
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def check_simple_trading_status():
    """Check simple trading status"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autonomous-simple/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data')
        return None
    except:
        return None

def start_simple_autonomous_trading():
    """Start simple autonomous trading"""
    try:
        response = requests.post(f"{BASE_URL}/api/v1/autonomous-simple/start", timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('success', False), data.get('message', 'Started')
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def test_simple_system():
    """Test simple autonomous system"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autonomous-simple/test", timeout=20)
        if response.status_code == 200:
            data = response.json()
            return data.get('success', False), data.get('message', 'Test completed')
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def compare_systems():
    """Compare simple vs complex orchestrator"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== SYSTEM COMPARISON ==={Colors.RESET}")
    
    # Check complex orchestrator
    print(f"\n{Colors.BOLD}Complex Orchestrator:{Colors.RESET}")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            complex_data = data.get('data', {})
            print(f"  Status: {Colors.GREEN if complex_data.get('is_active') else Colors.RED}{'ACTIVE' if complex_data.get('is_active') else 'INACTIVE'}{Colors.RESET}")
            print(f"  Strategies: {len(complex_data.get('active_strategies', []))}")
            print(f"  Trades: {complex_data.get('total_trades', 0)}")
            print(f"  System Ready: {complex_data.get('system_ready', False)}")
        else:
            print(f"  Status: {Colors.RED}ERROR{Colors.RESET}")
    except Exception as e:
        print(f"  Status: {Colors.RED}FAILED ({str(e)}){Colors.RESET}")
    
    # Check simple trader
    print(f"\n{Colors.BOLD}Simple Trader:{Colors.RESET}")
    simple_status = check_simple_trading_status()
    if simple_status:
        print(f"  Status: {Colors.GREEN if simple_status.get('is_active') else Colors.RED}{'ACTIVE' if simple_status.get('is_active') else 'INACTIVE'}{Colors.RESET}")
        print(f"  Strategies: {len(simple_status.get('active_strategies', []))}")
        print(f"  Trades: {simple_status.get('total_trades', 0)}")
        print(f"  System Ready: {simple_status.get('system_ready', False)}")
    else:
        print(f"  Status: {Colors.YELLOW}NOT AVAILABLE{Colors.RESET}")

def main():
    print(f"{Colors.BOLD}{Colors.CYAN}=== SIMPLE AUTONOMOUS TRADING SYSTEM ==={Colors.RESET}\n")
    
    # Step 1: Compare systems
    compare_systems()
    
    # Step 2: Test simple system
    print(f"\n{Colors.BOLD}1. Testing Simple System Components...{Colors.RESET}")
    test_success, test_message = test_simple_system()
    
    if test_success:
        print(f"{Colors.GREEN}✓ Simple system test passed{Colors.RESET}")
        print(f"  Message: {test_message}")
    else:
        print(f"{Colors.RED}✗ Simple system test failed{Colors.RESET}")
        print(f"  Error: {test_message}")
        print(f"\n{Colors.YELLOW}⚠️ Simple system not ready - check TrueData and Zerodha connections{Colors.RESET}")
        return
    
    # Step 3: Check if already running
    print(f"\n{Colors.BOLD}2. Checking Simple Trading Status...{Colors.RESET}")
    status = check_simple_trading_status()
    
    if status and status.get('is_active'):
        print(f"{Colors.GREEN}✓ Simple trading is already active!{Colors.RESET}")
        print(f"  Session ID: {status.get('session_id', 'Unknown')}")
        print(f"  Active strategies: {len(status.get('active_strategies', []))}")
        print(f"  Total trades: {status.get('total_trades', 0)}")
        return
    
    # Step 4: Start simple trading
    print(f"\n{Colors.BOLD}3. Starting Simple Autonomous Trading...{Colors.RESET}")
    success, message = start_simple_autonomous_trading()
    
    if success:
        print(f"{Colors.GREEN}✓ Simple trading started successfully!{Colors.RESET}")
        print(f"  Message: {message}")
    else:
        print(f"{Colors.RED}✗ Failed to start simple trading{Colors.RESET}")
        print(f"  Error: {message}")
        return
    
    # Step 5: Verify simple trading is active
    print(f"\n{Colors.BOLD}4. Verifying Simple Trading Status...{Colors.RESET}")
    time.sleep(3)  # Wait a moment
    
    status = check_simple_trading_status()
    if status and status.get('is_active'):
        print(f"{Colors.GREEN}✓ Simple trading is now ACTIVE!{Colors.RESET}")
        print(f"\n{Colors.BOLD}Simple Trading System Status:{Colors.RESET}")
        print(f"  Session ID: {status.get('session_id', 'Unknown')}")
        print(f"  Active strategies: {status.get('active_strategies', [])}")
        print(f"  Total trades: {status.get('total_trades', 0)}")
        print(f"  System ready: {status.get('system_ready', False)}")
        print(f"\n{Colors.GREEN}🎉 Simple system is ready for live trading!{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠️ Simple trading might still be initializing...{Colors.RESET}")
        print(f"Check the simple system status in a few moments.")
    
    # Step 6: Final comparison
    print(f"\n{Colors.BOLD}5. Final System Comparison...{Colors.RESET}")
    compare_systems()

if __name__ == "__main__":
    main() 