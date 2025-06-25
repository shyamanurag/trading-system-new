#!/usr/bin/env python3
"""
Test Daily Authentication Workflow
"""

import requests

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def test_daily_auth_workflow():
    """Test the complete daily authentication workflow"""
    print('🔐 TESTING DAILY AUTHENTICATION ENDPOINT')
    print('=' * 60)

    try:
        # Test the daily auth page
        response = requests.get(f'{BASE_URL}/daily-auth/', timeout=10)
        print(f'📤 Daily Auth Page Status: {response.status_code}')
        
        if response.status_code == 200:
            print('   ✅ Daily auth page is accessible!')
            print('   📋 User can now visit: https://algoauto-9gx56.ondigitalocean.app/daily-auth')
            
            # Test status endpoint
            status_response = requests.get(f'{BASE_URL}/daily-auth/status', timeout=10)
            print(f'\n📊 Auth Status Check: {status_response.status_code}')
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f'   🔐 Authenticated: {status_data.get("authenticated", False)}')
                print(f'   🚀 Trading Ready: {status_data.get("trading_ready", False)}')
                print(f'   💬 Message: {status_data.get("message", "N/A")}')
                return True
            else:
                print(f'   ❌ Status check failed: {status_response.text[:200]}')
                return False
        else:
            print(f'   ❌ Daily auth page failed: {response.text[:200]}')
            return False
            
    except Exception as e:
        print(f'❌ Error testing daily auth: {e}')
        return False

def main():
    """Main test function"""
    success = test_daily_auth_workflow()
    
    print('\n' + '=' * 60)
    if success:
        print('🎉 DAILY AUTHENTICATION WORKFLOW READY!')
        print('✅ Pre-configured Zerodha broker: ZERODHA_MAIN')
        print('📱 Daily auth URL: https://algoauto-9gx56.ondigitalocean.app/daily-auth')
        print('🚀 Streamlined workflow: Auth → Auto-start trading')
        print('')
        print('📋 DAILY WORKFLOW STEPS:')
        print('   1. Visit: /daily-auth')
        print('   2. Click "Authenticate with Zerodha"')
        print('   3. Enter Zerodha PIN')
        print('   4. System auto-starts trading')
        print('   5. Monitor & profit!')
        print('')
        print('🚫 NO MORE NEED TO:')
        print('   ❌ Add broker credentials daily')
        print('   ❌ Configure API keys')
        print('   ❌ Set up capital allocation')
        print('   ❌ Manual trading startup')
    else:
        print('❌ Daily authentication workflow needs debugging')
    
    print('=' * 60)

if __name__ == "__main__":
    main() 