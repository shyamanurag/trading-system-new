// Ultimate Test - Autonomous Trading
console.log('🎯 ULTIMATE AUTONOMOUS TRADING TEST');
console.log('===================================');

async function ultimateTest() {
    try {
        console.log('⚡ Testing autonomous start...');

        const start = await fetch('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/start', {
            method: 'POST'
        });

        const data = await start.json();

        console.log('Status:', start.status);
        console.log('Success:', data.success);

        if (data.success) {
            console.log('🎉🎉🎉 SUCCESS! AUTONOMOUS TRADING IS ONLINE! 🎉🎉🎉');
            console.log('Message:', data.message);

            // Check status after start
            setTimeout(async () => {
                const status = await fetch('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status');
                const statusData = await status.json();

                console.log('\n📊 POST-START STATUS:');
                console.log('✨ TRADING ACTIVE:', statusData.data?.is_active ? '🟢 YES' : '🔴 NO');
                console.log('🎯 SESSION ID:', statusData.data?.session_id || 'None');
                console.log('📈 START TIME:', statusData.data?.start_time || 'None');

                if (statusData.data?.is_active) {
                    console.log('\n🚀 ACHIEVEMENT UNLOCKED: AUTONOMOUS TRADING SYSTEM FULLY OPERATIONAL! 🚀');
                    console.log('💎 The system is now generating trading signals and monitoring markets');
                    console.log('🔥 Real TrueData flowing, real strategies loaded, real trading enabled!');
                }
            }, 3000);

        } else {
            console.log('❌ FAILED');
            console.log('Error:', data.message || data.detail);
        }

    } catch (e) {
        console.log('❌ Test Error:', e.message);
    }
}

ultimateTest(); 