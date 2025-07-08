// Test broker initialization specifically
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

console.log('🔍 BROKER INITIALIZATION TEST');
console.log('==============================');

async function testBrokerChain() {
    console.log('\n1️⃣ Testing Zerodha Status...');
    try {
        const res = await fetch(`${BASE_URL}/auth/zerodha/status`);
        console.log(`Status: ${res.status}`);
        if (res.status === 200) {
            const data = await res.json();
            console.log(`   🔐 Authenticated: ${data.authenticated}`);
            console.log(`   👤 User: ${data.profile?.user_name || 'Unknown'}`);
        }
    } catch (e) {
        console.log(`   Error: ${e.message}`);
    }

    console.log('\n2️⃣ Testing Strategy Status...');
    try {
        const res = await fetch(`${BASE_URL}/api/v1/autonomous/strategies`);
        console.log(`Status: ${res.status}`);
        if (res.status === 200) {
            const data = await res.json();
            console.log(`   📊 Strategies Available: ${Object.keys(data.data || {}).length}`);
            console.log(`   🧠 Strategy Names: ${Object.keys(data.data || {}).join(', ')}`);
        }
    } catch (e) {
        console.log(`   Error: ${e.message}`);
    }

    console.log('\n3️⃣ Testing Market Data...');
    try {
        const res = await fetch(`${BASE_URL}/api/v1/truedata/truedata/status`);
        console.log(`TrueData Status: ${res.status}`);

        // Try alternative market data endpoint
        const res2 = await fetch(`${BASE_URL}/api/v1/market/indices`);
        console.log(`Market Indices Status: ${res2.status}`);
        if (res2.status === 200) {
            const data = await res2.json();
            console.log(`   📈 Market Data Available: ${data.success || false}`);
        }
    } catch (e) {
        console.log(`   Error: ${e.message}`);
    }

    console.log('\n4️⃣ Simulating Start with Detailed Error...');
    try {
        const res = await fetch(`${BASE_URL}/api/v1/autonomous/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        console.log(`Start Status: ${res.status}`);
        const text = await res.text();
        console.log(`Response Body: ${text}`);

        try {
            const data = JSON.parse(text);
            console.log(`Parsed Response:`, JSON.stringify(data, null, 2));
        } catch (e) {
            console.log(`Could not parse as JSON`);
        }
    } catch (e) {
        console.log(`   Error: ${e.message}`);
    }

    console.log('\n5️⃣ Testing After Start Attempt...');
    try {
        const res = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
        const data = await res.json();
        console.log(`   🎯 Is Active: ${data.data?.is_active || false}`);
        console.log(`   🆔 Session: ${data.data?.session_id || 'None'}`);
        console.log(`   📊 System Ready: ${data.data?.system_ready || false}`);
    } catch (e) {
        console.log(`   Error: ${e.message}`);
    }
}

testBrokerChain(); 