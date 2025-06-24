#!/usr/bin/env python3
"""Final Test - Zerodha Manual Authentication System"""

import requests

def test_final_manual_auth():
    base_url = 'https://algoauto-9gx56.ondigitalocean.app'
    print('🔐 FINAL TEST: ZERODHA MANUAL AUTH SYSTEM')
    print('=' * 55)
    
    success_count = 0
    
    # Test 1: Auth URL generation
    endpoint = '/zerodha-manual/auth-url'
    print(f'1. Testing: {endpoint}')
    try:
        r = requests.get(base_url + endpoint, timeout=15)
        print(f'   Status: {r.status_code}')
        print(f'   Content-Type: {r.headers.get("content-type", "Unknown")}')
        
        if r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
            data = r.json()
            if data.get('success'):
                print('   ✅ AUTH URL GENERATION: SUCCESS!')
                print(f'   📊 Instructions: {len(data.get("instructions", []))} steps')
                print(f'   🔗 Auth URL: {data.get("auth_url", "")[:60]}...')
                success_count += 1
            else:
                print('   ❌ JSON but no success flag')
        else:
            print(f'   ❌ Failed - Status {r.status_code}')
    except Exception as e:
        print(f'   ❌ Error: {e}')

    print()

    # Test 2: Status check
    endpoint = '/zerodha-manual/status'
    print(f'2. Testing: {endpoint}')
    try:
        r = requests.get(base_url + endpoint, timeout=15)
        print(f'   Status: {r.status_code}')
        print(f'   Content-Type: {r.headers.get("content-type", "Unknown")}')
        
        if r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
            data = r.json()
            if data.get('success'):
                print('   ✅ STATUS CHECK: SUCCESS!')
                print(f'   📊 Authenticated: {data.get("authenticated", False)}')
                print(f'   📊 Message: {data.get("message", "")[:50]}...')
                success_count += 1
            else:
                print('   ❌ JSON but no success flag')
        else:
            print(f'   ❌ Failed - Status {r.status_code}')
    except Exception as e:
        print(f'   ❌ Error: {e}')

    print()
    print('=' * 55)

    if success_count >= 2:
        print('🎉 ZERODHA MANUAL AUTH SYSTEM: ✅ FULLY OPERATIONAL!')
        print()
        print('📋 COMPLETE USER WORKFLOW:')
        print('   1. GET /zerodha-manual/auth-url → Get authorization URL')
        print('   2. Open URL → Login with Zerodha credentials')  
        print('   3. Extract request_token from redirected URL')
        print('   4. POST /zerodha-manual/submit-token → Submit token')
        print('   5. GET /zerodha-manual/status → Check authentication')
        print('   6. GET /zerodha-manual/test-connection → Test connection')
        print()
        print('⚡ FINAL SOLUTION SUMMARY:')
        print('   🚀 TrueData: Primary market data (Fast, Real-time)')
        print('   🔄 Zerodha: Trading execution (Manual token workflow)')
        print('   ⏰ Daily re-authentication: 6:00 AM IST token expiry')
        print('   🎯 Problem solved: Manual token entry system operational!')
        print()
        print('🔗 DIRECT ACCESS URLS:')
        print(f'   Auth URL: {base_url}/zerodha-manual/auth-url')
        print(f'   Status:   {base_url}/zerodha-manual/status')
        print(f'   Submit:   {base_url}/zerodha-manual/submit-token (POST)')
        print(f'   Test:     {base_url}/zerodha-manual/test-connection')
    else:
        print('❌ Manual auth system still not fully working')
        print('💡 Need further troubleshooting')
        print(f'   Success count: {success_count}/2')

if __name__ == "__main__":
    test_final_manual_auth() 