// Precise test for autonomous trading failure
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

console.log('🎯 PRECISE AUTONOMOUS TRADING DIAGNOSTIC');
console.log('========================================');

async function preciseTest() {
    try {
        // 1. Check if bypass is working
        console.log('\n1️⃣ Market Status Check (Bypass)...');
        const statusRes = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
        const statusData = await statusRes.json();

        console.log(`   Market Open Field: ${statusData.data?.market_open !== undefined ? statusData.data.market_open : 'MISSING'}`);
        console.log(`   System Ready: ${statusData.data?.system_ready || false}`);

        // 2. Check component readiness
        console.log('\n2️⃣ Component Check...');
        const strategiesRes = await fetch(`${BASE_URL}/api/v1/autonomous/strategies`);
        const strategiesData = await strategiesRes.json();
        console.log(`   Strategies: ${Object.keys(strategiesData.data || {}).length} loaded`);

        const riskRes = await fetch(`${BASE_URL}/api/v1/autonomous/risk`);
        const riskData = await riskRes.json();
        console.log(`   Risk Manager: ${riskData.data?.status || 'unknown'}`);

        // 3. Test initialization 
        console.log('\n3️⃣ Testing Autonomous Start...');
        const startRes = await fetch(`${BASE_URL}/api/v1/autonomous/start`, {
            method: 'POST'
        });

        console.log(`   Status: ${startRes.status}`);
        const startData = await startRes.json();
        console.log(`   Response: ${JSON.stringify(startData, null, 2)}`);

        if (startRes.status === 200) {
            console.log('\n✅ SUCCESS! Checking post-start status...');

            // Wait and check status
            setTimeout(async () => {
                const postRes = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
                const postData = await postRes.json();
                console.log('\n📊 POST-START STATUS:');
                console.log(`   Active: ${postData.data?.is_active ? '🟢 YES' : '🔴 NO'}`);
                console.log(`   Session: ${postData.data?.session_id || 'None'}`);
                console.log(`   Market Open: ${postData.data?.market_open || false}`);
            }, 2000);
        }

    } catch (e) {
        console.log(`Error: ${e.message}`);
    }
}

preciseTest(); 