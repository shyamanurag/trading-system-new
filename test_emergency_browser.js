// Browser Test for Emergency Market Data Fix
// Run this in browser console at: https://algoauto-9gx56.ondigitalocean.app

console.log("🧪 Testing Emergency Market Data Fix...");

async function testEmergencyFix() {
    const BASE_URL = "https://algoauto-9gx56.ondigitalocean.app";

    try {
        console.log("🔍 Testing live-data endpoint...");
        const response = await fetch(`${BASE_URL}/api/v1/market-data/live-data`);
        console.log("Status:", response.status);

        if (response.ok) {
            const data = await response.json();
            console.log("✅ SUCCESS! Emergency endpoint working:");
            console.log("- Symbol count:", data.symbol_count);
            console.log("- Source:", data.source);
            console.log("- Sample symbols:", Object.keys(data.data).slice(0, 3));
            console.log("- NIFTY price:", data.data.NIFTY?.ltp);
            console.log("- BANKNIFTY price:", data.data.BANKNIFTY?.ltp);

            if (data.source?.includes("EMERGENCY") || data.source?.includes("FALLBACK")) {
                console.log("🎯 EMERGENCY FIX CONFIRMED: Fallback data is being served!");
                return true;
            } else {
                console.log("❌ Still using TrueData - fallback not triggered");
                return false;
            }
        } else {
            const error = await response.json();
            console.log("❌ Still failing:", error);
            return false;
        }
    } catch (error) {
        console.log("❌ Network error:", error.message);
        return false;
    }
}

// Test both endpoints
async function testBothEndpoints() {
    console.log("\n=== Testing Emergency Market Data Fix ===");

    // Test 1: /api/v1/market-data/live-data
    console.log("\n1️⃣ Testing /api/v1/market-data/live-data");
    const result1 = await testEmergencyFix();

    // Test 2: /api/v1/market-data/live
    console.log("\n2️⃣ Testing /api/v1/market-data/live");
    try {
        const response = await fetch("https://algoauto-9gx56.ondigitalocean.app/api/v1/market-data/live");
        console.log("Status:", response.status);

        if (response.ok) {
            const data = await response.json();
            console.log("✅ /live endpoint working:");
            console.log("- Symbol count:", data.symbol_count);
            console.log("- Source:", data.source);
        } else {
            const error = await response.json();
            console.log("❌ /live endpoint failing:", error);
        }
    } catch (error) {
        console.log("❌ /live endpoint error:", error.message);
    }

    // Summary
    console.log("\n=== SUMMARY ===");
    if (result1) {
        console.log("🎉 EMERGENCY FIX WORKING! Market data available for trading!");
        console.log("✅ Trading system should now be able to generate signals!");
    } else {
        console.log("💥 Emergency fix still not working - may need more time for deployment");
    }
}

// Run both tests
testBothEndpoints(); 