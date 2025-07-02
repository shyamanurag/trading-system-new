// Symbol Expansion Test - After Deployment
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

console.log('🎯 SYMBOL EXPANSION VERIFICATION TEST');
console.log('=====================================');
console.log('Expected: 6 → 50+ symbols expansion');
console.log('Target: Up to 250 F&O symbols');
console.log('');

async function testSymbolExpansion() {
    try {
        // Wait for deployment to complete
        console.log('⏳ Waiting for deployment to complete...');
        await new Promise(resolve => setTimeout(resolve, 60000));

        console.log('1️⃣ Testing Autonomous Status...');
        const statusRes = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
        const statusData = await statusRes.json();

        console.log('Trading Active:', statusData.data?.is_active ? '✅ YES' : '❌ NO');
        console.log('System Ready:', statusData.data?.system_ready ? '✅ YES' : '❌ NO');
        console.log('Strategies:', statusData.data?.active_strategies?.length || 0);

        console.log('');
        console.log('2️⃣ Testing Strategy Endpoint for Symbol Info...');
        const stratRes = await fetch(`${BASE_URL}/api/v1/autonomous/strategies`);
        const stratData = await stratRes.json();

        console.log('Strategies Status:', stratRes.status);
        console.log('Strategy Count:', Object.keys(stratData.data || {}).length);

        if (stratData.data) {
            Object.keys(stratData.data).forEach(strategy => {
                const stratInfo = stratData.data[strategy];
                console.log(`📊 ${strategy}:`, JSON.stringify(stratInfo, null, 2));
            });
        }

        console.log('');
        console.log('3️⃣ Attempting to Start Trading to Test Symbol Loading...');
        const startRes = await fetch(`${BASE_URL}/api/v1/autonomous/start`, {
            method: 'POST'
        });
        const startData = await startRes.json();

        console.log('Start Status:', startRes.status);
        console.log('Start Success:', startData.success ? '✅ YES' : '❌ NO');

        if (startData.success) {
            console.log('✨ SUCCESS! Trading started - symbols should be loading');

            // Check status after start to see symbol activity
            setTimeout(async () => {
                console.log('');
                console.log('4️⃣ Post-Start Status Check...');

                const postStatus = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
                const postData = await postStatus.json();

                console.log('🔥 FINAL STATUS:');
                console.log('Trading Active:', postData.data?.is_active ? '🟢 LIVE' : '🔴 INACTIVE');
                console.log('Session ID:', postData.data?.session_id);
                console.log('Start Time:', postData.data?.start_time);
                console.log('Last Heartbeat:', postData.data?.last_heartbeat);

                console.log('');
                console.log('🎯 SYMBOL EXPANSION TEST COMPLETE');
                console.log('Check server logs for actual symbol counts...');

            }, 10000);
        } else {
            console.log('❌ Start failed:', startData.message || startData.detail);
        }

    } catch (error) {
        console.log('❌ Test error:', error.message);
    }
}

// Run the test
testSymbolExpansion(); 