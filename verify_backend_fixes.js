const axios = require('axios');

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';
const ZERODHA_TOKEN = 'xXkTfIytomux6QZCEd0LOyHYWamtxtLH';

async function testBackendFixes() {
    console.log('=== TESTING BACKEND FIXES ===\n');

    // Create axios instance 
    const api = axios.create({
        baseURL: BASE_URL,
        timeout: 30000,
        validateStatus: () => true // Don't throw on any status
    });

    try {
        // 1. Submit Zerodha token directly
        console.log('1. Submitting Zerodha token...');
        const tokenResponse = await api.post('/api/zerodha/submit-token', {
            request_token: ZERODHA_TOKEN
        });
        console.log(`Status: ${tokenResponse.status}`);
        if (tokenResponse.data.success) {
            console.log(`✓ Authenticated as: ${tokenResponse.data.user?.name} (${tokenResponse.data.user?.user_id})`);
        }
        console.log();

        // 2. Check orchestrator debug endpoint (our fix)
        console.log('2. Checking orchestrator debug endpoint...');
        const orchResponse = await api.get('/api/system/orchestrator-debug');
        console.log(`Status: ${orchResponse.status}`);
        if (orchResponse.status === 200) {
            const comp = orchResponse.data.components;
            console.log('Components (should be true now):');
            console.log(`  - zerodha_client: ${comp.zerodha_client}`);
            console.log(`  - is_running: ${comp.is_running}`);
            console.log(`  - risk_manager: ${comp.risk_manager}`);
            console.log(`  - position_tracker: ${comp.position_tracker}`);
            console.log(`  - strategies_loaded: ${comp.strategies_loaded}`);
        }
        console.log();

        // 3. Check risk metrics (our fix - added get_risk_metrics method)
        console.log('3. Checking risk metrics endpoint...');
        const riskResponse = await api.get('/api/risk/metrics');
        console.log(`Status: ${riskResponse.status} ${riskResponse.status === 200 ? '✓ FIXED!' : '✗ Still broken'}`);
        if (riskResponse.status === 200) {
            console.log('Response:', JSON.stringify(riskResponse.data).substring(0, 100) + '...');
        }
        console.log();

        // 4. Check elite recommendations (our fix)
        console.log('4. Checking elite recommendations...');
        const eliteResponse = await api.get('/api/elite/recommendations');
        console.log(`Status: ${eliteResponse.status} ${eliteResponse.status === 200 ? '✓ FIXED!' : '✗ Still broken'}`);
        if (eliteResponse.status === 200 && eliteResponse.data.recommendations) {
            console.log(`Found ${eliteResponse.data.recommendations.length} recommendations`);
        }
        console.log();

        // 5. Check new endpoints we added
        console.log('5. Checking newly added endpoints...');
        const endpoints = ['/api/positions', '/api/orders', '/api/holdings', '/api/margins'];
        for (const endpoint of endpoints) {
            const resp = await api.get(endpoint);
            console.log(`  ${endpoint}: ${resp.status} ${resp.status !== 404 ? '✓' : '✗'}`);
        }
        console.log();

        // 6. Check system status
        console.log('6. Checking system status...');
        const statusResp = await api.get('/api/system/status');
        if (statusResp.status === 200) {
            const strategies = statusResp.data.strategies?.length || 0;
            console.log(`Strategies loaded: ${strategies} ${strategies === 5 ? '✓ All 5!' : '✗'}`);
        }

        console.log('\n=== SUMMARY ===');
        console.log('Check the statuses above. All should show ✓ if fixes are deployed correctly.');

    } catch (error) {
        console.error('Error:', error.message);
    }
}

testBackendFixes(); 