// Debug deployed system initialization
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

console.log('🔍 DEBUGGING DEPLOYMENT INITIALIZATION');
console.log('=====================================');

async function debugDeployment() {
    const debugEndpoints = [
        '/api/v1/debug/orchestrator/status',
        '/api/v1/debug/initialization/status',
        '/api/debug/orchestrator',
        '/api/v1/debug/components',
        '/debug/orchestrator',
        '/api/v1/debug/system/ready'
    ];

    console.log('\n🔍 Testing Debug Endpoints...');
    for (const endpoint of debugEndpoints) {
        try {
            const res = await fetch(`${BASE_URL}${endpoint}`);
            console.log(`${endpoint}: ${res.status}`);
            if (res.status === 200) {
                const data = await res.json();
                console.log(`   ✅ Data:`, JSON.stringify(data, null, 2));
            }
        } catch (e) {
            console.log(`${endpoint}: ERROR - ${e.message}`);
        }
    }

    // Test manual initialization
    console.log('\n🚀 Testing Manual Force Initialization...');
    try {
        const res = await fetch(`${BASE_URL}/api/v1/debug/force-initialize`, { method: 'POST' });
        console.log(`Force Init Status: ${res.status}`);
        const data = await res.json();
        console.log('Force Init Result:', JSON.stringify(data, null, 2));
    } catch (e) {
        console.log(`Force Init Error: ${e.message}`);
    }
}

debugDeployment(); 