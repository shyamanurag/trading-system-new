// Check if deployment has latest changes
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

console.log('🔍 CHECKING DEPLOYMENT STATUS');
console.log('=============================');

(async () => {
    try {
        // Check root endpoint for build info
        console.log('\n1️⃣ Checking App Info...');
        const rootRes = await fetch(BASE_URL);
        const rootData = await rootRes.json();
        console.log('Root data:', rootData);

        // Check health endpoint
        console.log('\n2️⃣ Checking Health...');
        const healthRes = await fetch(`${BASE_URL}/health`);
        const healthData = await healthRes.json();
        console.log('Health:', healthData);

        // Check market status to see if bypass is active
        console.log('\n3️⃣ Testing Market Status (Bypass Check)...');
        const statusRes = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
        const statusData = await statusRes.json();
        const marketOpen = statusData.data?.market_open || false;

        console.log(`Market Open: ${marketOpen ? '✅ YES (BYPASS ACTIVE)' : '❌ NO (BYPASS NOT DEPLOYED)'}`);

        if (marketOpen) {
            console.log('\n🎉 DEPLOYMENT COMPLETE - Testing autonomous start...');

            const startRes = await fetch(`${BASE_URL}/api/v1/autonomous/start`, {
                method: 'POST'
            });

            console.log(`Start result: ${startRes.status}`);

            if (startRes.status === 200) {
                const startData = await startRes.json();
                console.log('✅ SUCCESS:', startData.message);
            } else {
                const errorData = await startRes.json();
                console.log('❌ ERROR:', errorData);
            }
        } else {
            console.log('\n⏳ Deployment still in progress - check again in 1-2 minutes');
        }

    } catch (e) {
        console.log('Error:', e.message);
    }
})(); 