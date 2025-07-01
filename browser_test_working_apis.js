// =============================================================================
// LIVE TRADING TEST - WORKING ENDPOINTS (Markets Open)
// =============================================================================

console.log("🚀 Testing Live Trading System - Working Endpoints");

const BASE_URL = window.location.origin;
const API_BASE = `${BASE_URL}/api/v1`;

async function testAPI(endpoint, method = 'GET') {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, { method });
        const data = await response.json();
        console.log(`✅ ${method} ${endpoint}:`, data);
        return { success: response.ok, data };
    } catch (error) {
        console.error(`❌ ${endpoint}:`, error);
        return { success: false, error };
    }
}

async function runTest() {
    console.log("\n🔍 CHECKING CURRENT STATUS:");

    // Test the working endpoints we see in logs
    await testAPI('/system/status');
    await testAPI('/autonomous/status');
    await testAPI('/broker/status');
    await testAPI('/positions/');

    console.log("\n🚀 ATTEMPTING TO START TRADING:");
    const startResult = await testAPI('/autonomous/start', 'POST');

    if (startResult.success) {
        console.log("✅ Start command sent!");
        await new Promise(r => setTimeout(r, 2000));
        await testAPI('/autonomous/status');
    }

    console.log("\n💰 CHECKING FOR TRADES:");
    await testAPI('/trades/today');
    await testAPI('/trades/active');

    console.log("\n📊 FINAL STATUS:");
    const finalStatus = await testAPI('/autonomous/status');

    if (finalStatus.data?.is_active) {
        console.log("🎉 AUTONOMOUS TRADING IS ACTIVE!");
    } else {
        console.log("⚠️ Autonomous trading not active yet");
    }
}

// Run the test
runTest(); 