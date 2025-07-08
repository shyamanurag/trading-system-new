/**
 * COMPONENT-SPECIFIC DIAGNOSTIC TEST
 * Try to identify which specific orchestrator component is failing during initialization
 */

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

async function testSpecificComponents() {
    console.log('🔍 COMPONENT-SPECIFIC DIAGNOSTIC TEST');
    console.log('='.repeat(60));

    // Test individual component endpoints if they exist
    const componentEndpoints = [
        // Market data
        '/api/market-data/status',
        '/api/v1/market-data/status',
        '/api/truedata/status',
        '/api/v1/truedata/status',

        // Risk management
        '/api/risk/status',
        '/api/v1/risk/status',

        // Positions
        '/api/positions',
        '/api/v1/positions',
        '/api/v1/autonomous/positions',

        // Performance/metrics
        '/api/v1/autonomous/performance',
        '/api/v1/autonomous/risk',

        // Strategy
        '/api/strategies',
        '/api/v1/strategies',
        '/api/v1/autonomous/strategies'
    ];

    console.log('📋 Testing component-specific endpoints...\n');

    const workingComponents = [];
    const failingComponents = [];

    for (const endpoint of componentEndpoints) {
        try {
            const response = await fetch(`${BASE_URL}${endpoint}`);

            if (response.status === 200) {
                workingComponents.push(endpoint);
                const data = await response.json();
                console.log(`✅ ${endpoint}`);
                console.log(`   Response: ${JSON.stringify(data, null, 2).substring(0, 150)}...`);
                console.log('');
            } else if (response.status === 500) {
                failingComponents.push({ endpoint, status: response.status });
                console.log(`💥 ${endpoint}: 500 ERROR`);
                const errorText = await response.text();
                console.log(`   Error: ${errorText.substring(0, 100)}...`);
                console.log('');
            } else if (response.status !== 404) {
                console.log(`❓ ${endpoint}: ${response.status}`);
            }
        } catch (error) {
            console.log(`🚫 ${endpoint}: ${error.message}`);
        }
    }

    // Test if we can get partial orchestrator status
    console.log('\n🔧 Testing orchestrator status approaches...');

    const statusApproaches = [
        {
            name: 'Direct Status Call',
            method: async () => {
                const response = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
                return await response.json();
            }
        },
        {
            name: 'Force Initialize Check',
            method: async () => {
                // Try to force initialization and see what specific error we get
                const response = await fetch(`${BASE_URL}/api/v1/autonomous/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ force: true, debug: true })
                });
                const text = await response.text();
                return { status: response.status, body: text };
            }
        }
    ];

    for (const approach of statusApproaches) {
        try {
            console.log(`\n📊 ${approach.name}:`);
            const result = await approach.method();
            console.log(JSON.stringify(result, null, 2));
        } catch (error) {
            console.log(`❌ ${approach.name} failed: ${error.message}`);
        }
    }

    console.log('\n' + '='.repeat(60));
    console.log('📊 COMPONENT ANALYSIS SUMMARY:');
    console.log(`✅ Working components: ${workingComponents.length}`);
    console.log(`💥 Failing components: ${failingComponents.length}`);

    if (workingComponents.length > 0) {
        console.log('\n✅ WORKING COMPONENTS:');
        workingComponents.forEach(comp => console.log(`  - ${comp}`));
    }

    if (failingComponents.length > 0) {
        console.log('\n💥 FAILING COMPONENTS:');
        failingComponents.forEach(({ endpoint, status }) => console.log(`  - ${endpoint}: ${status}`));
    }

    console.log('\n🎯 Next steps: Focus on failing components for detailed investigation');
}

// Run the component test
testSpecificComponents().catch(console.error); 