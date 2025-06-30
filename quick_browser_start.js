// 🚀 QUICK START AUTONOMOUS TRADING - Browser Console Script
// Copy this entire script and paste it into your browser console (F12 -> Console)

console.log("🚀 QUICK START AUTONOMOUS TRADING");

// Quick start function
async function quickStart() {
    const API = 'https://algoauto-9gx56.ondigitalocean.app/api/v1';

    console.log("1️⃣ Checking market status...");
    const market = await fetch(`${API}/market/market-status`).then(r => r.json());
    console.log(`📈 Market: ${market.status} at ${market.current_time}`);

    console.log("2️⃣ Checking trading status...");
    const status = await fetch(`${API}/autonomous/status`).then(r => r.json());
    const isActive = status.data?.is_active;
    console.log(`🤖 Trading Active: ${isActive}`);

    if (isActive) {
        console.log("✅ TRADING IS ALREADY RUNNING!");
        return;
    }

    console.log("3️⃣ Starting autonomous trading...");
    const start = await fetch(`${API}/autonomous/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });

    if (start.ok) {
        console.log("🎉 SUCCESS! Autonomous trading started!");

        // Start monitoring
        console.log("4️⃣ Starting monitor...");
        window.monitor = setInterval(async () => {
            const s = await fetch(`${API}/autonomous/status`).then(r => r.json());
            const active = s.data?.is_active;
            const pnl = s.data?.daily_pnl || 0;
            const positions = s.data?.active_positions?.length || 0;
            console.log(`${new Date().toLocaleTimeString()} - Trading: ${active ? '🟢' : '🔴'} | P&L: ${pnl} | Positions: ${positions}`);
        }, 30000);

        console.log("💡 To stop monitoring: clearInterval(window.monitor)");
        console.log("💡 To emergency stop trading: emergencyStop()");

    } else {
        const error = await start.json();
        console.log("❌ Failed to start trading:");
        console.log(error);
        console.log("🔧 Try running: completeTradingSetup() for advanced troubleshooting");
    }
}

// Emergency stop function
window.emergencyStop = async function () {
    const API = 'https://algoauto-9gx56.ondigitalocean.app/api/v1';
    const stop = await fetch(`${API}/autonomous/stop`, { method: 'POST' });
    if (stop.ok) {
        console.log("🛑 EMERGENCY STOP SUCCESSFUL");
        if (window.monitor) clearInterval(window.monitor);
    } else {
        console.log("❌ Emergency stop failed");
    }
}

// Run quick start
quickStart();

// Instructions
console.log("\n" + "=".repeat(50));
console.log("🎯 INSTRUCTIONS:");
console.log("1. If trading starts successfully, you'll see status updates every 30 seconds");
console.log("2. Monitor will show: Trading status, P&L, and position count");
console.log("3. Type 'emergencyStop()' to stop trading immediately");
console.log("4. Check your trading dashboard for detailed view");
console.log("=".repeat(50)); 