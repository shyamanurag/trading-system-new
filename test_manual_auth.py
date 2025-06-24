#!/usr/bin/env python3
"""Test Zerodha Manual Authentication System"""

import requests
import json

def test_manual_auth():
    base_url = 'https://algoauto-9gx56.ondigitalocean.app'
    print('🔐 TESTING ZERODHA MANUAL AUTH SYSTEM')
    print('=' * 50)
    
    success_count = 0
    
    # Test 1: Auth URL generation
    try:
        print('1. Testing auth URL generation...')
        r = requests.get(base_url + '/zerodha-manual/auth-url', timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                print('   ✅ Auth URL generated successfully')
                print('   📊 Instructions provided:', len(data.get('instructions', [])))
                print('   🔗 URL preview:', data.get('auth_url', '')[:60] + '...')
                success_count += 1
            else:
                print('   ❌ No success in response')
        else:
            print('   ❌ Status code:', r.status_code)
    except Exception as e:
        print('   ❌ Error:', str(e)[:50])

    # Test 2: Status check
    try:
        print('\n2. Testing authentication status...')
        r = requests.get(base_url + '/zerodha-manual/status', timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                print('   ✅ Status check working')
                print('   📊 Authenticated:', data.get('authenticated', False))
                print('   📊 Message:', data.get('message', '')[:60])
                success_count += 1
            else:
                print('   ❌ No success in response')
        else:
            print('   ❌ Status code:', r.status_code)
    except Exception as e:
        print('   ❌ Error:', str(e)[:50])

    # Results
    print('\n' + '=' * 50)
    if success_count >= 2:
        print('🎯 MANUAL AUTH SYSTEM STATUS: ✅ READY')
        print('\n📋 USER WORKFLOW:')
        print('   1. GET /zerodha-manual/auth-url - Get authorization URL')
        print('   2. Visit URL and login with Zerodha credentials')
        print('   3. Extract request_token from redirected URL')
        print('   4. POST /zerodha-manual/submit-token - Submit token')
        print('   5. GET /zerodha-manual/status - Check authentication')
        print('\n⚡ DATA SOURCES:')
        print('   🚀 TrueData: Primary (Fast, Real-time)')
        print('   🐌 Zerodha: Secondary (Slower, for trading)')
        print('   ⏰ Tokens expire daily at 6:00 AM IST')
        
        print('\n🔗 DIRECT LINKS:')
        print(f'   Auth URL: {base_url}/zerodha-manual/auth-url')
        print(f'   Status:   {base_url}/zerodha-manual/status')
        print(f'   Submit:   {base_url}/zerodha-manual/submit-token (POST)')
    else:
        print('❌ MANUAL AUTH SYSTEM: Some endpoints not working')
        print('⏳ System may still be deploying...')

if __name__ == "__main__":
    test_manual_auth() 