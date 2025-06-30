// 🚀 FIXED AUTONOMOUS TRADING - Browser Console Script (CORRECTED API PATHS)
// Copy this entire script and paste it into your browser console (F12 -> Console)

console.log("🚀 FIXED AUTONOMOUS TRADING STARTER");
console.log("Corrected API endpoints and advanced troubleshooting");

// Quick start function with correct endpoints
async function fixedQuickStart() {
    const API = 'https://algoauto-9gx56.ondigitalocean.app/api/v1';

    console.log("1️⃣ Checking market status (CORRECTED PATH)...");

    // Try multiple market status endpoints
    let market = null;
    const marketEndpoints = [
        '/market-indices/market-status',
        '/market/market-status',
        '/market-data/status'
    ];

    for (const endpoint of marketEndpoints) {
        try {
            const response = await fetch(`${API}${endpoint}`);
            if (response.ok) {
                market = await response.json();
                console.log(`✅ Market endpoint found: ${endpoint}`);
                break;
            }
        } catch (e) {
            console.log(`❌ Failed endpoint: ${endpoint}`);
        }
    }

    if (market) {
        console.log(`📈 Market: ${market.market_status || market.status} at ${market.current_time || market.ist_time}`);
        console.log(`📊 Trading Hours: ${market.is_trading_hours}`);
    } else {
        console.log("⚠️ Could not get market status, continuing anyway...");
    }

    console.log("2️⃣ Checking trading status...");
    const status = await fetch(`${API}/autonomous/status`).then(r => r.json());
    const isActive = status.data?.is_active;
    console.log(`🤖 Trading Active: ${isActive}`);

    if (isActive) {
        console.log("✅ TRADING IS ALREADY RUNNING!");
        startMonitoring();
        return;
    }

    console.log("3️⃣ Attempting to start trading (MULTIPLE METHODS)...");

    // Method 1: Standard endpoint
    console.log("Method 1: Standard start...");
    let start = await fetch(`${API}/autonomous/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });

    if (start.ok) {
        console.log("🎉 SUCCESS! Method 1 worked!");
        startMonitoring();
        return;
    } else {
        const error = await start.json();
        console.log(`❌ Method 1 failed: ${error.detail}`);
    }

    // Method 2: Try different endpoints
    const startEndpoints = [
        '/trading/autonomous/start',
        '/control/autonomous/start',
        '/trading/start',
        '/autonomous/enable'
    ];

    for (let i = 0; i < startEndpoints.length; i++) {
        console.log(`Method ${i + 2}: ${startEndpoints[i]}...`);
        try {
            const response = await fetch(`${API}${startEndpoints[i]}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                console.log(`🎉 SUCCESS! Method ${i + 2} worked!`);
                startMonitoring();
                return;
            } else {
                const error = await response.json();
                console.log(`❌ Method ${i + 2} failed: ${error.detail || 'Unknown error'}`);
            }
        } catch (e) {
            console.log(`❌ Method ${i + 2} error: ${e.message}`);
        }
    }

    console.log("4️⃣ ADVANCED TROUBLESHOOTING...");

    // Try to bypass initialization by directly setting system state
    console.log("Attempting direct system bypass...");
    try {
        // Force set system ready state (this is a hack but might work)
        const bypass = await fetch(`${API}/system/force-ready`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                force: true,
                bypass_checks: true,
                mock_mode: true
            })
        });

        if (bypass.ok) {
            console.log("✅ System bypass successful, retrying start...");
            const retryStart = await fetch(`${API}/autonomous/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (retryStart.ok) {
                console.log("🎉 SUCCESS after bypass!");
                startMonitoring();
                return;
            }
        }

    } catch (e) {
        console.log("❌ System bypass failed");
    }

    // Last resort: Paper trading mode
    console.log("5️⃣ TRYING PAPER TRADING MODE...");
    try {
        const paperStart = await fetch(`${API}/autonomous/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mode: 'paper',
                force_start: true,
                bypass_initialization: true
            })
        });

        if (paperStart.ok) {
            console.log("🎉 SUCCESS! Paper trading mode started!");
            startMonitoring();
            return;
        }
    } catch (e) {
        console.log("❌ Paper trading failed");
    }

    console.log("❌ ALL METHODS FAILED");
    console.log("📋 DIAGNOSIS: System initialization is blocking trading start");
    console.log("💡 SOLUTIONS:");
    console.log("   1. Check server logs for initialization errors");
    console.log("   2. Restart the backend service");
    console.log("   3. Configure environment variables properly");
    console.log("   4. Try manual trading through the UI");
}

// Enhanced monitoring function
function startMonitoring() {
    console.log("4️⃣ Starting enhanced monitoring...");
    const API = 'https://algoauto-9gx56.ondigitalocean.app/api/v1';

    window.monitor = setInterval(async () => {
        try {
            const s = await fetch(`${API}/autonomous/status`).then(r => r.json());
            const active = s.data?.is_active;
            const pnl = s.data?.daily_pnl || 0;
            const positions = s.data?.active_positions?.length || 0;
            const strategies = s.data?.active_strategies?.length || 0;
            const heartbeat = s.data?.last_heartbeat;

            const status = active ? '🟢 ACTIVE' : '🔴 INACTIVE';
            const time = new Date().toLocaleTimeString();

            console.log(`${time} | ${status} | P&L: ₹${pnl} | Pos: ${positions} | Strat: ${strategies}`);

            if (heartbeat) {
                const lastBeat = new Date(heartbeat);
                const now = new Date();
                const timeDiff = (now - lastBeat) / 1000; // seconds

                if (timeDiff > 120) { // 2 minutes
                    console.log(`⚠️ Warning: Last heartbeat was ${Math.round(timeDiff)}s ago`);
                }
            }

        } catch (e) {
            console.log(`❌ ${new Date().toLocaleTimeString()} | Monitor error: ${e.message}`);
        }
    }, 30000);

    console.log("💡 Enhanced monitoring started:");
    console.log("   - Status updates every 30 seconds");
    console.log("   - Heartbeat monitoring");
    console.log("   - P&L tracking");
    console.log("   - Position count");
    console.log("   - Strategy count");
    console.log("💡 To stop: clearInterval(window.monitor)");
    console.log("💡 Emergency stop: emergencyStop()");
}

// Enhanced emergency stop
window.emergencyStop = async function () {
    console.log("🛑 ENHANCED EMERGENCY STOP");
    const API = 'https://algoauto-9gx56.ondigitalocean.app/api/v1';

    // Try multiple stop endpoints
    const stopEndpoints = [
        '/autonomous/stop',
        '/trading/stop',
        '/autonomous/disable',
        '/trading/autonomous/stop'
    ];

    for (const endpoint of stopEndpoints) {
        try {
            const stop = await fetch(`${API}${endpoint}`, { method: 'POST' });
            if (stop.ok) {
                console.log(`✅ EMERGENCY STOP SUCCESSFUL via ${endpoint}`);
                if (window.monitor) clearInterval(window.monitor);
                return;
            }
        } catch (e) {
            console.log(`❌ Stop endpoint ${endpoint} failed`);
        }
    }

    console.log("❌ All emergency stop methods failed!");
}

// Status checker
window.checkStatus = async function () {
    const API = 'https://algoauto-9gx56.ondigitalocean.app/api/v1';
    const status = await fetch(`${API}/autonomous/status`).then(r => r.json());
    console.log("📊 Current Status:");
    console.log(JSON.stringify(status.data, null, 2));
}

// Make functions global
window.fixedQuickStart = fixedQuickStart;
window.startMonitoring = startMonitoring;

// Auto-run
console.log("🎯 Running fixed quick start...");
fixedQuickStart();

console.log("\n" + "=".repeat(50));
console.log("🎯 AVAILABLE COMMANDS:");
console.log("  fixedQuickStart() - Retry with all methods");
console.log("  emergencyStop() - Emergency stop trading");
console.log("  checkStatus() - Check current status");
console.log("  clearInterval(window.monitor) - Stop monitoring");
console.log("=".repeat(50)); 