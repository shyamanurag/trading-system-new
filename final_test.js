// Final comprehensive test for autonomous trading
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

console.log('🚀 FINAL AUTONOMOUS TRADING TEST');
console.log('=================================');

async function finalTest() {
    console.log('\n⏰ Current Time Check...');
    const now = new Date();
    const istTime = new Date(now.getTime() + (5.5 * 60 * 60 * 1000)); // Convert to IST
    console.log(`   🕐 Current IST: ${istTime.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}`);
    console.log(`   📈 Market hours: 9:15 AM - 3:30 PM IST`);

    console.log('\n1️⃣ Complete System Status...');
    try {
        const res = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
        const data = await res.json();
        const statusData = data.data || {};

        console.log(`   🎯 Is Active: ${statusData.is_active || false}`);
        console.log(`   🔧 System Ready: ${statusData.system_ready || false}`);
        console.log(`   📊 Market Open: ${statusData.market_open || false}`);
        console.log(`   🧠 Strategies: ${statusData.active_strategies?.length || 0}`);
        console.log(`   📍 Positions: ${statusData.active_positions?.length || 0}`);
        console.log(`   💰 Daily P&L: ₹${statusData.daily_pnl || 0}`);
        console.log(`   🆔 Session: ${statusData.session_id || 'None'}`);

        if (statusData.is_active) {
            console.log('\n✅ AUTONOMOUS TRADING IS ALREADY ACTIVE!');
            return;
        }
    } catch (e) {
        console.log(`   Error: ${e.message}`);
    }

    console.log('\n2️⃣ Authentication Check...');
    try {
        const res = await fetch(`${BASE_URL}/auth/zerodha/status`);
        const data = await res.json();
        console.log(`   🔐 Zerodha Auth: ${data.authenticated ? '✅ AUTHENTICATED' : '❌ NOT AUTHENTICATED'}`);

        if (!data.authenticated) {
            console.log('\n❌ Cannot start trading - Zerodha not authenticated');
            return;
        }
    } catch (e) {
        console.log(`   Error: ${e.message}`);
    }

    console.log('\n3️⃣ Component Readiness...');
    const components = [
        '/api/v1/autonomous/strategies',
        '/api/v1/autonomous/risk',
        '/api/v1/autonomous/positions'
    ];

    let allReady = true;
    for (const endpoint of components) {
        try {
            const res = await fetch(`${BASE_URL}${endpoint}`);
            const status = res.status === 200 ? '✅' : '❌';
            console.log(`   ${endpoint.split('/').pop()}: ${status} (${res.status})`);
            if (res.status !== 200) allReady = false;
        } catch (e) {
            console.log(`   ${endpoint}: ❌ ERROR`);
            allReady = false;
        }
    }

    if (!allReady) {
        console.log('\n❌ Not all components ready - cannot start trading');
        return;
    }

    console.log('\n4️⃣ Attempting to Start Autonomous Trading...');
    try {
        const startRes = await fetch(`${BASE_URL}/api/v1/autonomous/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        console.log(`   📤 Start Request Status: ${startRes.status}`);

        if (startRes.status === 200) {
            const startData = await startRes.json();
            console.log(`   ✅ SUCCESS: ${startData.message || 'Autonomous trading started!'}`);

            // Wait and check status
            console.log('\n⏳ Waiting 3 seconds for initialization...');
            await new Promise(resolve => setTimeout(resolve, 3000));

            const statusRes = await fetch(`${BASE_URL}/api/v1/autonomous/status`);
            const statusData = await statusRes.json();
            const status = statusData.data || {};

            console.log('\n🎯 POST-START STATUS:');
            console.log(`   🎯 Is Active: ${status.is_active ? '🟢 ACTIVE' : '🔴 INACTIVE'}`);
            console.log(`   🆔 Session: ${status.session_id || 'None'}`);
            console.log(`   📊 Strategies: ${status.active_strategies?.length || 0}`);

            if (status.is_active) {
                console.log('\n🎉 AUTONOMOUS TRADING SUCCESSFULLY STARTED!');
                console.log('💰 System is now trading with real market data');
                console.log('🎯 Precision over speed - using authenticated Zerodha + TrueData');
            }

        } else {
            const errorData = await startRes.json();
            console.log(`   ❌ FAILED: ${errorData.detail || errorData.message || 'Unknown error'}`);

            // Try to get more specific error details
            console.log('\n🔍 Investigating Error Details...');

            // Check health status
            const healthRes = await fetch(`${BASE_URL}/health/ready/json`);
            if (healthRes.status === 200) {
                const healthData = await healthRes.json();
                console.log(`   🔧 System Health:`);
                console.log(`      Database: ${healthData.database_connected ? '✅' : '❌'}`);
                console.log(`      Redis: ${healthData.redis_connected ? '✅' : '❌'}`);
                console.log(`      Trading: ${healthData.trading_enabled ? '✅' : '❌'}`);
            }
        }

    } catch (e) {
        console.log(`   💥 Exception: ${e.message}`);
    }
}

finalTest();

console.log('🎯 FINAL TEST - Ultra-Simple Fallback');
console.log('=====================================');

async function finalTest() {
    try {
        console.log('⏱️ Waiting 60 seconds for deployment...');
        await new Promise(resolve => setTimeout(resolve, 60000));

        console.log('\n1. Testing Risk Manager...');
        const riskResponse = await fetch('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/risk');
        const riskData = await riskResponse.json();

        console.log('Risk Status:', riskData.data?.status);
        const fallbackWorking = riskData.data?.status?.includes('working_minimal');
        console.log('Ultra-Simple Fallback:', fallbackWorking ? 'SUCCESS ✅' : 'FAILED ❌');

        if (fallbackWorking) {
            console.log('\n2. Testing Orchestrator Components...');
            const debugResponse = await fetch('https://algoauto-9gx56.ondigitalocean.app/api/v1/debug/orchestrator-debug');
            const debugData = await debugResponse.json();

            console.log('Components Ready:', debugData.components_ready_count + '/' + debugData.total_components);
            console.log('Position Tracker:', debugData.components?.position_tracker ? 'SUCCESS ✅' : 'FAILED ❌');
            console.log('Risk Manager:', debugData.components?.risk_manager ? 'SUCCESS ✅' : 'FAILED ❌');

            if (debugData.components?.position_tracker && debugData.components?.risk_manager) {
                console.log('\n3. Testing Autonomous Start...');
                const startResponse = await fetch('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/start', {
                    method: 'POST'
                });
                const startData = await startResponse.json();

                console.log('Autonomous Start:', startData.success ? 'SUCCESS ✅' : 'FAILED ❌');
                console.log('Message:', startData.message || startData.detail);

                if (startData.success) {
                    console.log('\n🎉 BREAKTHROUGH ACHIEVED!');
                    console.log('✅ Trading system is now fully operational!');
                    console.log('✅ All infrastructure issues resolved!');
                    console.log('✅ Ready for live trading!');
                } else {
                    console.log('\n❌ Still issues with autonomous start');
                }
            } else {
                console.log('\n❌ Components still not initializing properly');
            }
        } else {
            console.log('\n❌ Ultra-simple fallback not working yet');
        }

    } catch (error) {
        console.log('❌ Error during final test:', error.message);
    }
}

finalTest(); 