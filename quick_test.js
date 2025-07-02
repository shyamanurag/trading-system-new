// Quick test for deployed autonomous trading system
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

console.log('🚀 AUTONOMOUS TRADING DEPLOYMENT TEST');
console.log('=====================================');

async function quickTest() {
    try {
        // Test 1: Status
        console.log('\n1️⃣ Autonomous Status Check...');
        const statusRes = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
        const statusData = await statusRes.json();
        console.log(`   Status: ${statusRes.status}`);
        console.log(`   Active: ${statusData.data?.is_active || false}`);
        console.log(`   P&L: ₹${statusData.data?.daily_pnl || 0}`);

        // Test 2: Start Trading  
        console.log('\n2️⃣ Start Trading Test...');
        const startRes = await fetch(`${BASE_URL}/api/v1/autonomous/start`, { method: 'POST' });
        const startData = await startRes.json();
        console.log(`   Status: ${startRes.status}`);
        console.log(`   Success: ${startData.success || false}`);
        console.log(`   Message: ${startData.message || 'None'}`);
        console.log(`   Detail: ${startData.detail || 'None'}`);

        if (startRes.status === 200) {
            console.log('\n✅ SUCCESS! Autonomous trading started!');
        } else {
            console.log('\n❌ FAILED! Error details above');
        }

    } catch (error) {
        console.log(`\n💥 Exception: ${error.message}`);
    }
}

quickTest(); 