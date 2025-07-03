// Test script for deployed Zerodha refresh system
const BASE_URL = 'https://trading-system-new.ondigitalocean.app';
const API_BASE = `${BASE_URL}/api/zerodha/refresh`;

async function testHealth() {
    console.log('Testing health endpoint...');
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        console.log('Health check result:', data);
        return response.ok;
    } catch (error) {
        console.log('Health check failed:', error.message);
        return false;
    }
}

async function testStatus() {
    console.log('\nTesting status endpoint...');
    try {
        const response = await fetch(`${API_BASE}/status?user_id=QSW899`);
        const data = await response.json();
        console.log('Status result:', data);
        return response.ok;
    } catch (error) {
        console.log('Status check failed:', error.message);
        return false;
    }
}

async function testRefreshToken() {
    console.log('\nTesting refresh token endpoint...');
    try {
        const response = await fetch(`${API_BASE}/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force_refresh: false, user_id: 'QSW899' })
        });
        const data = await response.json();
        console.log('Refresh token result:', data);
        return response.ok;
    } catch (error) {
        console.log('Refresh token failed:', error.message);
        return false;
    }
}

async function testConnection() {
    console.log('\nTesting connection endpoint...');
    try {
        const response = await fetch(`${API_BASE}/test-connection`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: 'QSW899' })
        });
        const data = await response.json();
        console.log('Connection test result:', data);
        return response.ok;
    } catch (error) {
        console.log('Connection test failed:', error.message);
        return false;
    }
}

async function testMainHealth() {
    console.log('\nTesting main app health...');
    try {
        const response = await fetch(`${BASE_URL}/health`);
        const data = await response.json();
        console.log('Main health result:', data);
        return response.ok;
    } catch (error) {
        console.log('Main health failed:', error.message);
        return false;
    }
}

async function runTests() {
    console.log('Starting Zerodha refresh system tests...');
    console.log('Base URL:', BASE_URL);
    console.log('API Base:', API_BASE);

    const results = {
        mainHealth: await testMainHealth(),
        health: await testHealth(),
        status: await testStatus(),
        refreshToken: await testRefreshToken(),
        connection: await testConnection()
    };

    console.log('\nTest Results:');
    Object.entries(results).forEach(([test, passed]) => {
        console.log(`${test}: ${passed ? 'PASS' : 'FAIL'}`);
    });

    const passed = Object.values(results).filter(Boolean).length;
    console.log(`\nOverall: ${passed}/${Object.keys(results).length} tests passed`);
}

runTests().catch(console.error); 