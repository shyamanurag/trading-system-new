const axios = require('axios');

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';
const ZERODHA_TOKEN = 'xXkTfIytomux6QZCEd0LOyHYWamtxtLH';

// Admin credentials for login
const ADMIN_CREDENTIALS = {
    username: 'admin',
    password: 'admin123'
};

async function testRedeployedApp() {
    console.log('=== TESTING REDEPLOYED APP WITH FIXES ===\n');

    try {
        // 1. Login as admin
        console.log('1. Logging in as admin...');
        const loginResponse = await axios.post(`${BASE_URL}/api/users/login`, ADMIN_CREDENTIALS);
        const authToken = loginResponse.data.token;
        console.log('✓ Login successful\n');

        // Create axios instance with auth
        const api = axios.create({
            baseURL: BASE_URL,
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            timeout: 30000,
            validateStatus: () => true // Don't throw on any status
        });

        // 2. Submit Zerodha token
        console.log('2. Submitting Zerodha token...');
        const tokenResponse = await api.post('/api/zerodha/submit-token', {
            request_token: ZERODHA_TOKEN
        });
        console.log(`Zerodha token submission: ${tokenResponse.status}`,
            tokenResponse.data.success ? '✓ Success' : '✗ Failed');
        if (tokenResponse.data.user) {
            console.log(`Authenticated as: ${tokenResponse.data.user.name} (${tokenResponse.data.user.user_id})`);
        }
        console.log();

        // 3. Check orchestrator debug (FIXED: should show true values now)
        console.log('3. Checking orchestrator debug endpoint (FIX VERIFICATION)...');
        const orchResponse = await api.get('/api/system/orchestrator-debug');
        console.log(`Orchestrator debug: ${orchResponse.status}`);
        if (orchResponse.status === 200) {
            const components = orchResponse.data.components;
            console.log('Components status:');
            console.log(`  - zerodha_client: ${components.zerodha_client} ${components.zerodha_client ? '✓' : '✗'}`);
            console.log(`  - is_running: ${components.is_running} ${components.is_running ? '✓' : '✗'}`);
            console.log(`  - strategies_loaded: ${components.strategies_loaded}`);
            console.log(`  - risk_manager: ${components.risk_manager} ${components.risk_manager ? '✓' : '✗'}`);
            console.log(`  - position_tracker: ${components.position_tracker} ${components.position_tracker ? '✓' : '✗'}`);
        }
        console.log();

        // 4. Check risk metrics (FIXED: should not return 500 error)
        console.log('4. Checking risk metrics endpoint (FIX VERIFICATION)...');
        const riskResponse = await api.get('/api/risk/metrics');
        console.log(`Risk metrics: ${riskResponse.status} ${riskResponse.status === 200 ? '✓ Fixed!' : '✗ Still broken'}`);
        if (riskResponse.status === 200) {
            console.log('Risk metrics data:', JSON.stringify(riskResponse.data, null, 2));
        }
        console.log();

        // 5. Check elite recommendations (FIXED: should return recommendations, not 503)
        console.log('5. Checking elite recommendations endpoint (FIX VERIFICATION)...');
        const eliteResponse = await api.get('/api/elite/recommendations');
        console.log(`Elite recommendations: ${eliteResponse.status} ${eliteResponse.status === 200 ? '✓ Fixed!' : '✗ Still broken'}`);
        if (eliteResponse.status === 200) {
            console.log(`Found ${eliteResponse.data.recommendations?.length || 0} recommendations`);
        }
        console.log();

        // 6. Check new endpoints (FIXED: should exist now)
        console.log('6. Checking newly added endpoints (FIX VERIFICATION)...');
        const newEndpoints = [
            '/api/positions',
            '/api/orders',
            '/api/holdings',
            '/api/margins'
        ];

        for (const endpoint of newEndpoints) {
            const response = await api.get(endpoint);
            console.log(`  ${endpoint}: ${response.status} ${response.status !== 404 ? '✓ Exists!' : '✗ Not found'}`);
        }
        console.log();

        // 7. Check strategies loaded count (should be 5)
        console.log('7. Checking strategies count...');
        const statusResponse = await api.get('/api/system/status');
        if (statusResponse.status === 200) {
            const strategiesCount = statusResponse.data.strategies?.length || 0;
            console.log(`Strategies loaded: ${strategiesCount} ${strategiesCount === 5 ? '✓ All 5 loaded!' : '✗ Missing strategies'}`);
            if (statusResponse.data.strategies) {
                statusResponse.data.strategies.forEach(s => console.log(`  - ${s.name}: ${s.status}`));
            }
        }
        console.log();

        // 8. Summary of fixes
        console.log('=== FIX VERIFICATION SUMMARY ===');
        console.log('1. Orchestrator components: Check above - should show true values');
        console.log('2. Risk metrics endpoint: Should return 200, not 500');
        console.log('3. Elite recommendations: Should return 200 with recommendations');
        console.log('4. New endpoints: Should all exist (not 404)');
        console.log('5. Strategies: Should load all 5 strategies');

    } catch (error) {
        console.error('Test error:', error.message);
        if (error.response) {
            console.error('Response:', error.response.status, error.response.data);
        }
    }
}

// Run the test
testRedeployedApp(); 