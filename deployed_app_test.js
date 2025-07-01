/**
 * DEPLOYED APP TEST - Find exact pinpoint issue
 * Tests the live DigitalOcean deployment to identify the specific failure
 */

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

async function testDeployedApp() {
    console.log('🔍 DEPLOYED APP DIAGNOSTIC TEST');
    console.log('='.repeat(50));

    // Test 1: Verify working endpoints are still working
    console.log('\n📊 STEP 1: Verify working endpoints');
    const workingEndpoints = [
        '/api/v1/autonomous/status',
        '/api/market/indices',
        '/api/market/market-status'
    ];

    for (const endpoint of workingEndpoints) {
        try {
            const response = await fetch(`${BASE_URL}${endpoint}`);
            const status = response.status === 200 ? '✅ OK' : `❌ ${response.status}`;
            console.log(`  ${status} - ${endpoint}`);
        } catch (error) {
            console.log(`  ❌ ERROR - ${endpoint}: ${error.message}`);
        }
    }

    // Test 2: Analyze the failing start endpoint in detail
    console.log('\n🎯 STEP 2: Detailed analysis of failing start endpoint');

    try {
        console.log('📞 Calling /api/v1/autonomous/start...');
        const startTime = Date.now();

        const response = await fetch(`${BASE_URL}/api/v1/autonomous/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });

        const endTime = Date.now();
        const duration = endTime - startTime;

        console.log(`⏱️  Response Time: ${duration}ms`);
        console.log(`📊 Status Code: ${response.status}`);
        console.log(`📝 Headers:`, Object.fromEntries(response.headers.entries()));

        const responseText = await response.text();
        console.log(`📄 Response Body: ${responseText}`);

        // Try to parse as JSON
        try {
            const jsonData = JSON.parse(responseText);
            console.log(`🎯 Parsed JSON:`, JSON.stringify(jsonData, null, 2));
        } catch (parseError) {
            console.log(`❌ JSON Parse Error: ${parseError.message}`);
        }

    } catch (error) {
        console.log(`❌ Request Error: ${error.message}`);
        console.log(`🔍 Error Details:`, error);
    }

    // Test 3: Test related orchestrator endpoints for debugging
    console.log('\n🔧 STEP 3: Test orchestrator debug endpoints');

    const debugEndpoints = [
        '/api/debug/orchestrator/status',
        '/api/debug/orchestrator/components',
        '/api/debug/initialization-status'
    ];

    for (const endpoint of debugEndpoints) {
        try {
            const response = await fetch(`${BASE_URL}${endpoint}`);
            if (response.status === 200) {
                const data = await response.json();
                console.log(`✅ ${endpoint}:`, JSON.stringify(data, null, 2));
            } else {
                console.log(`❌ ${endpoint}: ${response.status} - ${await response.text()}`);
            }
        } catch (error) {
            console.log(`🚫 ${endpoint}: Not available or error - ${error.message}`);
        }
    }

    console.log('\n' + '='.repeat(50));
    console.log('🎯 DIAGNOSTIC COMPLETE');
}

// Run the test
testDeployedApp().catch(console.error); 