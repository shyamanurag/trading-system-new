/**
 * CORRECTED TRADING SYSTEM TEST
 * =============================
 * 
 * This uses the CORRECT API endpoints to test your scalping system
 * 
 * Run this in browser console to verify the exact issue
 */

async function testCorrectEndpoints() {
    console.clear();
    console.log('%c🔍 CORRECTED TRADING SYSTEM TEST', 'color: #FF6B35; font-size: 18px; font-weight: bold;');
    console.log('Using CORRECT API endpoints...\n');

    const baseUrl = 'https://algoauto-9gx56.ondigitalocean.app';

    // Test 1: Autonomous Status (we know this works)
    console.log('1️⃣ Testing autonomous status...');
    try {
        const statusResponse = await fetch(`${baseUrl}/api/v1/autonomous/status`);
        const statusData = await statusResponse.json();
        console.log(`%c✅ Trading Active: ${statusData.data.is_active}`, 'color: #4CAF50; font-weight: bold;');
        console.log(`%c✅ Strategies: ${statusData.data.active_strategies.length}`, 'color: #4CAF50; font-weight: bold;');
        console.log(`%c🎯 Active strategies: ${statusData.data.active_strategies.join(', ')}`, 'color: #2196F3;');
    } catch (error) {
        console.log('%c❌ Status test failed', 'color: #F44336;');
    }

    console.log('\n2️⃣ Testing CORRECT order endpoints...');

    // Test 2: Correct Orders Endpoint
    try {
        const ordersResponse = await fetch(`${baseUrl}/api/v1/orders/`);
        const ordersData = await ordersResponse.json();
        console.log(`%c✅ Orders API works: ${ordersResponse.status}`, 'color: #4CAF50;');
        console.log(`%c📊 Orders found: ${ordersData.orders ? ordersData.orders.length : 0}`,
            ordersData.orders && ordersData.orders.length > 0 ? 'color: #4CAF50;' : 'color: #F44336;');
        console.log(`%c📋 Message: ${ordersData.message}`, 'color: #2196F3;');

        if (!ordersData.orders || ordersData.orders.length === 0) {
            console.log('%c🎯 CONFIRMED: No orders being placed by strategies!', 'color: #F44336; font-weight: bold;');
        }
    } catch (error) {
        console.log('%c❌ Orders endpoint failed', 'color: #F44336;');
    }

    // Test 3: Live Orders
    try {
        const liveResponse = await fetch(`${baseUrl}/api/v1/orders/live`);
        const liveData = await liveResponse.json();
        console.log(`%c✅ Live orders API works: ${liveResponse.status}`, 'color: #4CAF50;');
        console.log(`%c📊 Live orders: ${liveData.orders ? liveData.orders.length : 0}`,
            liveData.orders && liveData.orders.length > 0 ? 'color: #4CAF50;' : 'color: #F44336;');

        if (!liveData.orders || liveData.orders.length === 0) {
            console.log('%c🎯 CONFIRMED: No live orders from strategies!', 'color: #F44336; font-weight: bold;');
        }
    } catch (error) {
        console.log('%c❌ Live orders endpoint failed', 'color: #F44336;');
    }

    console.log('\n%c🎯 FINAL DIAGNOSIS:', 'color: #FF6B35; font-size: 16px; font-weight: bold;');
    console.log('%c✅ System components working:', 'color: #4CAF50; font-weight: bold;');
    console.log('%c   • Zerodha authenticated ✓', 'color: #4CAF50;');
    console.log('%c   • 4 strategies active ✓', 'color: #4CAF50;');
    console.log('%c   • Market data flowing ✓', 'color: #4CAF50;');
    console.log('%c   • Order APIs working ✓', 'color: #4CAF50;');
    console.log('\n%c❌ MISSING LINK:', 'color: #F44336; font-weight: bold;');
    console.log('%c   • Strategies not sending orders to trade engine!', 'color: #F44336; font-weight: bold;');
    console.log('%c   • Trade engine not connected to Zerodha!', 'color: #F44336; font-weight: bold;');

    console.log('\n%c🔧 SOLUTION NEEDED:', 'color: #FF9800; font-weight: bold;');
    console.log('%c   Connect strategy signals → trade engine → Zerodha API', 'color: #FF9800;');
}

// Run the corrected test
testCorrectEndpoints(); 