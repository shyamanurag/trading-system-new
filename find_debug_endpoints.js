/**
 * DISCOVER AVAILABLE DEBUG ENDPOINTS
 * Find endpoints that might show component status or initialization details
 */

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

async function findDebugEndpoints() {
    console.log('🔍 DISCOVERING AVAILABLE DEBUG ENDPOINTS');
    console.log('='.repeat(50));

    // Potential debug/health endpoints to test
    const potentialEndpoints = [
        // System health endpoints
        '/api/health',
        '/api/system/health',
        '/api/system/status',
        '/api/v1/system/health',
        '/api/v1/system/status',

        // Orchestrator endpoints
        '/api/orchestrator/status',
        '/api/v1/orchestrator/status',
        '/api/orchestrator/health',

        // Debug endpoints
        '/api/debug',
        '/api/v1/debug',
        '/api/debug/status',
        '/api/v1/debug/status',

        // Component status endpoints
        '/api/components',
        '/api/v1/components',
        '/api/trading/status',
        '/api/v1/trading/status',

        // Monitoring endpoints
        '/api/monitoring',
        '/api/v1/monitoring',
        '/api/metrics',
        '/api/v1/metrics',

        // Database/connection endpoints
        '/api/database/health',
        '/api/v1/database/health',
        '/api/connections',
        '/api/v1/connections'
    ];

    console.log(`📋 Testing ${potentialEndpoints.length} potential endpoints...\n`);

    const workingEndpoints = [];
    const notFoundEndpoints = [];
    const errorEndpoints = [];

    for (const endpoint of potentialEndpoints) {
        try {
            const response = await fetch(`${BASE_URL}${endpoint}`);

            if (response.status === 200) {
                workingEndpoints.push(endpoint);
                console.log(`✅ FOUND: ${endpoint}`);

                // Try to get response data
                try {
                    const data = await response.json();
                    console.log(`   Data: ${JSON.stringify(data, null, 2).substring(0, 200)}...`);
                } catch (e) {
                    const text = await response.text();
                    console.log(`   Text: ${text.substring(0, 100)}...`);
                }
                console.log('');
            } else if (response.status === 404) {
                notFoundEndpoints.push(endpoint);
            } else {
                errorEndpoints.push({ endpoint, status: response.status });
                console.log(`❓ ${endpoint}: ${response.status}`);
            }
        } catch (error) {
            console.log(`💥 ${endpoint}: ERROR - ${error.message}`);
        }
    }

    console.log('\n' + '='.repeat(50));
    console.log('📊 SUMMARY:');
    console.log(`✅ Working endpoints: ${workingEndpoints.length}`);
    console.log(`❌ Not found (404): ${notFoundEndpoints.length}`);
    console.log(`❓ Other errors: ${errorEndpoints.length}`);

    if (workingEndpoints.length > 0) {
        console.log('\n🎯 WORKING DEBUG ENDPOINTS:');
        workingEndpoints.forEach(ep => console.log(`  - ${ep}`));
    }

    if (errorEndpoints.length > 0) {
        console.log('\n❓ ENDPOINTS WITH ERRORS:');
        errorEndpoints.forEach(({ endpoint, status }) => console.log(`  - ${endpoint}: ${status}`));
    }
}

// Run the discovery
findDebugEndpoints().catch(console.error); 