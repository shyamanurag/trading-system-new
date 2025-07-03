#!/usr/bin/env python3
"""
Start Autonomous Trading System
Checks authentication status and starts trading
"""

import requests
import json
import time

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def check_auth_status():
    """Check if Zerodha is authenticated"""
    try:
        response = requests.get(f"{BASE_URL}/auth/zerodha/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('authenticated', False), data
        return False, None
    except:
        return False, None

def start_autonomous_trading():
    """Start the autonomous trading system"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/autonomous/start",
            json={},
            timeout=30
        )
        return response.status_code, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return 'ERROR', str(e)

def check_trading_status():
    """Check current trading status"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                return data['data']
        return None
    except:
        return None

def check_orchestrator_components():
    """Check orchestrator component status"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/debug/orchestrator-debug", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def main():
    print(f"{Colors.BOLD}{Colors.CYAN}=== AUTONOMOUS TRADING SYSTEM STARTER ==={Colors.RESET}\n")
    
    # Step 1: Check authentication
    print(f"{Colors.BOLD}1. Checking Zerodha Authentication...{Colors.RESET}")
    is_auth, auth_data = check_auth_status()
    
    if not is_auth:
        print(f"{Colors.RED}✗ Not authenticated with Zerodha{Colors.RESET}")
        print(f"\nPlease authenticate first:")
        print(f"1. Visit: https://kite.zerodha.com/connect/login?api_key=vc9ft4zpknynpm3u")
        print(f"2. Login to Zerodha")
        print(f"3. You'll be redirected back automatically")
        return
    
    print(f"{Colors.GREEN}✓ Authenticated{Colors.RESET}")
    if auth_data and 'session' in auth_data:
        print(f"  User: {auth_data.get('user_id', 'Unknown')}")
        print(f"  Expires: {auth_data['session'].get('expires_at', 'Unknown')}")
    
    # Step 2: Check current trading status
    print(f"\n{Colors.BOLD}2. Checking Trading Status...{Colors.RESET}")
    status = check_trading_status()
    
    if status:
        is_active = status.get('is_active', False)
        if is_active:
            print(f"{Colors.GREEN}✓ Trading is already active!{Colors.RESET}")
            print(f"  Session ID: {status.get('session_id', 'Unknown')}")
            print(f"  Active strategies: {len(status.get('active_strategies', []))}")
            return
        else:
            print(f"{Colors.YELLOW}Trading is NOT active{Colors.RESET}")
    
    # Step 3: Check orchestrator components
    print(f"\n{Colors.BOLD}3. Checking System Components...{Colors.RESET}")
    orch_status = check_orchestrator_components()
    
    if orch_status and 'components' in orch_status:
        components = orch_status['components']
        ready_count = orch_status.get('components_ready_count', 0)
        total = orch_status.get('total_components', 0)
        
        print(f"Components ready: {ready_count}/{total}")
        for key, value in components.items():
            status_icon = f"{Colors.GREEN}✓{Colors.RESET}" if value else f"{Colors.RED}✗{Colors.RESET}"
            print(f"  {key}: {status_icon}")
    
    # Step 4: Start trading
    print(f"\n{Colors.BOLD}4. Starting Autonomous Trading...{Colors.RESET}")
    status_code, response = start_autonomous_trading()
    
    if status_code == 200:
        print(f"{Colors.GREEN}✓ Trading started successfully!{Colors.RESET}")
        if isinstance(response, dict):
            print(f"  Message: {response.get('message', 'Trading active')}")
    else:
        print(f"{Colors.RED}✗ Failed to start trading{Colors.RESET}")
        print(f"  Status: {status_code}")
        print(f"  Response: {response}")
    
    # Step 5: Verify trading is active
    print(f"\n{Colors.BOLD}5. Verifying Trading Status...{Colors.RESET}")
    time.sleep(2)  # Wait a moment
    
    status = check_trading_status()
    if status and status.get('is_active'):
        print(f"{Colors.GREEN}✓ Trading is now ACTIVE!{Colors.RESET}")
        print(f"\n{Colors.BOLD}Trading System Status:{Colors.RESET}")
        print(f"  Session ID: {status.get('session_id', 'Unknown')}")
        print(f"  Active strategies: {status.get('active_strategies', [])}")
        print(f"  Market status: {status.get('market_status', 'Unknown')}")
        print(f"\n{Colors.GREEN}🎉 System is ready for live trading!{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠ Trading might still be initializing...{Colors.RESET}")
        print(f"Check the dashboard in a few moments.")

if __name__ == "__main__":
    main() 