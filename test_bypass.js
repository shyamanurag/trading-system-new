// Test market hours bypass deployment
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

console.log('🚀 TESTING MARKET HOURS BYPASS DEPLOYMENT');
console.log('==========================================');

async function testBypass() {
    console.log('\n1️⃣ Testing Market Status After Bypass...');
    try {
        const res = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
        const data = await res.json();
        const marketOpen = data.data?.market_open || false;

        console.log(`   🌐 App Reports Market Open: ${marketOpen ? '✅ YES' : '❌ NO'}`);

        if (marketOpen) {
            console.log('   ✅ BYPASS WORKING - Market detected as OPEN');
        } else {
            console.log('   ❌ BYPASS NOT YET DEPLOYED - Still showing closed');
            console.log('   ⏳ Wait 1-2 minutes for deployment completion');
            return;
        }
    } catch (e) {
        console.log(`   Error: ${e.message}`);
        return;
    }

    console.log('\n2️⃣ Testing Autonomous Trading Start...');
    try {
        const startRes = await fetch(`${BASE_URL}/api/v1/autonomous/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        console.log(`   📤 Start Status: ${startRes.status}`);

        if (startRes.status === 200) {
            const startData = await startRes.json();
            console.log(`   ✅ SUCCESS: ${startData.message || 'Autonomous trading started!'}`);

            // Check status after start
            console.log('\n⏳ Waiting 3 seconds for initialization...');
            await new Promise(resolve => setTimeout(resolve, 3000));

            const statusRes = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
            const statusData = await statusRes.json();
            const status = statusData.data || {};

            console.log('\n🎯 POST-START STATUS:');
            console.log(`   🎯 Is Active: ${status.is_active ? '🟢 ACTIVE' : '🔴 INACTIVE'}`);
            console.log(`   🆔 Session: ${status.session_id || 'None'}`);
            console.log(`   📊 Market Open: ${status.market_open ? '✅ YES' : '❌ NO'}`);
            console.log(`   🧠 Strategies: ${status.active_strategies?.length || 0}`);
            console.log(`   💰 Daily P&L: ₹${status.daily_pnl || 0}`);

            if (status.is_active) {
                console.log('\n🎉 AUTONOMOUS TRADING SUCCESSFULLY STARTED!');
                console.log('💰 System is now running with market hours bypass');
                console.log('🔧 Ready to test trading functionality');
            } else {
                console.log('\n⚠️ Trading start reported success but system still inactive');
            }

        } else {
            const errorData = await startRes.json();
            console.log(`   ❌ FAILED: ${errorData.detail || errorData.message || 'Unknown error'}`);
            console.log('   💡 The bypass may not have deployed yet, or there\'s another issue');
        }

    } catch (e) {
        console.log(`   💥 Exception: ${e.message}`);
    }
}

testBypass(); 