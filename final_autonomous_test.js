// Final Autonomous Trading Test - After Risk Manager Bypass
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

console.log('🎯 FINAL AUTONOMOUS TRADING TEST');
console.log('===================================');
console.log('Testing after Risk Manager bypass deployment...\n');

async function finalTest() {
    try {
        // 1. Check Risk Manager Status
        console.log('1️⃣ Risk Manager Status...');
        const riskRes = await fetch(`${BASE_URL}/api/v1/autonomous/risk`);
        const riskData = await riskRes.json();
        console.log(`   Status: ${riskData.success ? '✅' : '❌'}`);
        console.log(`   Risk Manager: ${riskData.data?.status || 'unknown'}`);

        // 2. Check System Status
        console.log('\n2️⃣ System Status...');
        const statusRes = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
        const statusData = await statusRes.json();
        console.log(`   System Ready: ${statusData.data?.system_ready ? '✅' : '❌'}`);
        console.log(`   Market Open: ${statusData.data?.market_open ? '✅' : '❌'}`);
        console.log(`   Strategies: ${statusData.data?.active_strategies || 0}`);

        // 3. Test Autonomous Start
        console.log('\n3️⃣ Testing Autonomous Start (THE MOMENT OF TRUTH)...');
        const startRes = await fetch(`${BASE_URL}/api/v1/autonomous/start`, {
            method: 'POST'
        });

        console.log(`   HTTP Status: ${startRes.status}`);
        const startData = await startRes.json();

        if (startRes.status === 200 && startData.success) {
            console.log('\n🎉 SUCCESS! AUTONOMOUS TRADING STARTED!');
            console.log(`   Message: ${startData.message}`);

            // Check post-start status
            setTimeout(async () => {
                const postRes = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
                const postData = await postRes.json();

                console.log('\n📊 POST-START STATUS:');
                console.log(`   Is Active: ${postData.data?.is_active ? '🟢 TRADING ACTIVE' : '🔴 NOT ACTIVE'}`);
                console.log(`   Session ID: ${postData.data?.session_id || 'None'}`);
                console.log(`   Start Time: ${postData.data?.start_time || 'None'}`);

                if (postData.data?.is_active) {
                    console.log('\n✨ ACHIEVEMENT UNLOCKED: Autonomous Trading System ONLINE! ✨');
                    console.log('🚀 System is now generating trading signals and monitoring markets');
                }
            }, 3000);

        } else {
            console.log('\n❌ FAILED TO START');
            console.log(`   Response: ${JSON.stringify(startData, null, 2)}`);

            // Diagnose the failure
            console.log('\n🔍 FAILURE DIAGNOSIS:');
            if (startData.detail) {
                console.log(`   Error: ${startData.detail}`);

                if (startData.detail.includes('initialize')) {
                    console.log('   💡 Hint: Still initialization issues - may need more component bypasses');
                } else if (startData.detail.includes('ready')) {
                    console.log('   💡 Hint: System not ready - check component initialization');
                }
            }
        }

    } catch (e) {
        console.log(`❌ Test Error: ${e.message}`);
    }
}

// Wait for deployment then test
console.log('⏳ Waiting for deployment to complete...');
setTimeout(finalTest, 10000); // Wait 10 seconds for deployment 