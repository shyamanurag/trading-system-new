// Test database and Redis connectivity
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

console.log('🔍 CONNECTION DIAGNOSTIC TEST');
console.log('=============================');

async function testConnections() {
    const endpoints = [
        '/health',
        '/ready',
        '/health/ready/json',
        '/api/v1/database/health',
        '/api/database/health',
        '/api/health/database',
        '/api/v1/system/health',
        '/api/v1/monitoring/system-status',
        '/status',
        '/api/status'
    ];

    console.log('\n🔍 Testing Available Endpoints...');
    for (const endpoint of endpoints) {
        try {
            const res = await fetch(`${BASE_URL}${endpoint}`);
            console.log(`${endpoint}: ${res.status}`);
            if (res.status === 200) {
                try {
                    const data = await res.json();
                    if (data.database_connected !== undefined) {
                        console.log(`   📊 Database: ${data.database_connected ? '✅' : '❌'}`);
                    }
                    if (data.redis_connected !== undefined) {
                        console.log(`   📊 Redis: ${data.redis_connected ? '✅' : '❌'}`);
                    }
                    if (data.components) {
                        console.log(`   📊 Components:`, data.components);
                    }
                } catch (e) {
                    console.log(`   📝 Response: ${await res.text()}`);
                }
            }
        } catch (e) {
            console.log(`${endpoint}: ERROR - ${e.message}`);
        }
    }

    // Try to access specific component status
    console.log('\n🔧 Testing Component Status...');
    const componentEndpoints = [
        '/api/v1/autonomous/positions',
        '/api/v1/autonomous/performance',
        '/api/v1/autonomous/strategies',
        '/api/v1/autonomous/risk'
    ];

    for (const endpoint of componentEndpoints) {
        try {
            const res = await fetch(`${BASE_URL}${endpoint}`);
            console.log(`${endpoint}: ${res.status}`);
            if (res.status === 200) {
                const data = await res.json();
                console.log(`   ✅ Working`);
            } else if (res.status === 500) {
                const data = await res.json();
                console.log(`   ❌ 500: ${data.detail || 'Unknown error'}`);
            }
        } catch (e) {
            console.log(`${endpoint}: ERROR - ${e.message}`);
        }
    }
}

testConnections(); 