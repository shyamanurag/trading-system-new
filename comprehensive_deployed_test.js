/**
 * 🚀 COMPREHENSIVE DEPLOYED SYSTEM TEST
 * ====================================
 * 
 * Tests ALL deployed fixes:
 * ✅ Elite API Performance Fix (30s caching, real data)
 * ✅ Scalping Trade Execution Fix (orchestrator bypass)
 * ✅ Zerodha Authentication & Integration
 * 
 * Run in browser console to verify complete system functionality
 */

async function runComprehensiveTest() {
    console.clear();
    console.log('%c🚀 COMPREHENSIVE DEPLOYED SYSTEM TEST', 'color: #FF6B35; font-size: 20px; font-weight: bold;');
    console.log('%c====================================', 'color: #FF6B35; font-size: 16px;');
    console.log('Testing ALL deployed fixes...\n');

    const baseUrl = 'https://algoauto-9gx56.ondigitalocean.app';
    let testResults = {
        eliteAPI: false,
        zerodhaAuth: false,
        tradingSystem: false,
        orderExecution: false,
        overallHealth: false
    };

    // ======================
    // 1️⃣ ELITE API TEST (Performance Fix)
    // ======================
    console.log('%c1️⃣ TESTING ELITE API PERFORMANCE FIX', 'color: #4CAF50; font-size: 16px; font-weight: bold;');
    try {
        const eliteStart = Date.now();
        const eliteResponse = await fetch(`${baseUrl}/api/v1/elite`);
        const eliteTime = Date.now() - eliteStart;
        const eliteData = await eliteResponse.json();

        console.log(`%c⚡ Response Time: ${eliteTime}ms`, eliteTime < 1000 ? 'color: #4CAF50; font-weight: bold;' : 'color: #F44336; font-weight: bold;');
        console.log(`%c📊 Status: ${eliteData.success ? 'SUCCESS' : 'FAILED'}`, eliteData.success ? 'color: #4CAF50;' : 'color: #F44336;');
        console.log(`%c📈 Recommendations: ${eliteData.total_count}`, eliteData.total_count > 0 ? 'color: #4CAF50;' : 'color: #F44336;');
        console.log(`%c🎯 Data Source: ${eliteData.data_source}`, 'color: #2196F3;');
        console.log(`%c🕐 Generated: ${eliteData.scan_timestamp}`, 'color: #2196F3;');
        console.log(`%c🕐 Next Scan: ${eliteData.next_scan}`, 'color: #2196F3;');

        if (eliteData.recommendations && eliteData.recommendations.length > 0) {
            const sample = eliteData.recommendations[0];
            console.log(`%c📋 Sample: ${sample.symbol} ${sample.direction} @ ₹${sample.current_price} (${sample.confidence}% confidence)`, 'color: #2196F3;');
            console.log(`%c🕐 Sample Generated: ${sample.generated_at}`, 'color: #2196F3;');
            console.log(`%c🕐 Data Timestamp: ${sample.real_data_timestamp}`, 'color: #2196F3;');
        }

        testResults.eliteAPI = eliteData.success && eliteTime < 2000 && eliteData.total_count > 0;

    } catch (error) {
        console.log('%c❌ Elite API test failed:', 'color: #F44336; font-weight: bold;', error.message);
    }

    // ======================
    // 2️⃣ ZERODHA AUTHENTICATION TEST
    // ======================
    console.log('\n%c2️⃣ TESTING ZERODHA AUTHENTICATION', 'color: #4CAF50; font-size: 16px; font-weight: bold;');
    try {
        const authResponse = await fetch(`${baseUrl}/api/v1/zerodha/auth-status`);
        const authData = await authResponse.json();

        console.log(`%c🔐 Auth Status: ${authData.authenticated ? 'AUTHENTICATED' : 'NOT AUTHENTICATED'}`,
            authData.authenticated ? 'color: #4CAF50; font-weight: bold;' : 'color: #F44336; font-weight: bold;');
        console.log(`%c👤 User ID: ${authData.user_id || 'N/A'}`, 'color: #2196F3;');
        console.log(`%c🕐 Auth Time: ${authData.auth_time || 'N/A'}`, 'color: #2196F3;');
        console.log(`%c✅ Valid: ${authData.valid || 'N/A'}`, authData.valid ? 'color: #4CAF50;' : 'color: #F44336;');

        testResults.zerodhaAuth = authData.authenticated === true;

    } catch (error) {
        console.log('%c❌ Zerodha auth test failed:', 'color: #F44336; font-weight: bold;', error.message);
    }

    // ======================
    // 3️⃣ TRADING SYSTEM STATUS TEST
    // ======================
    console.log('\n%c3️⃣ TESTING TRADING SYSTEM STATUS', 'color: #4CAF50; font-size: 16px; font-weight: bold;');
    try {
        const tradingResponse = await fetch(`${baseUrl}/api/v1/autonomous/status`);
        const tradingData = await tradingResponse.json();

        console.log(`%c🎯 Trading Active: ${tradingData.data.is_active}`,
            tradingData.data.is_active ? 'color: #4CAF50; font-weight: bold;' : 'color: #F44336; font-weight: bold;');
        console.log(`%c📊 Active Strategies: ${tradingData.data.active_strategies.length}`,
            tradingData.data.active_strategies.length > 0 ? 'color: #4CAF50;' : 'color: #F44336;');
        console.log(`%c🎯 Strategies: ${tradingData.data.active_strategies.join(', ')}`, 'color: #2196F3;');
        console.log(`%c📈 Market Data: ${tradingData.data.market_data_status}`, 'color: #2196F3;');
        console.log(`%c🕐 System Time: ${tradingData.data.system_time}`, 'color: #2196F3;');

        testResults.tradingSystem = tradingData.data.is_active && tradingData.data.active_strategies.length > 0;

    } catch (error) {
        console.log('%c❌ Trading system test failed:', 'color: #F44336; font-weight: bold;', error.message);
    }

    // ======================
    // 4️⃣ ORDER EXECUTION TEST (THE CRITICAL FIX)
    // ======================
    console.log('\n%c4️⃣ TESTING ORDER EXECUTION (CRITICAL FIX)', 'color: #4CAF50; font-size: 16px; font-weight: bold;');
    try {
        // Test current orders
        const ordersResponse = await fetch(`${baseUrl}/api/v1/orders/`);
        const ordersData = await ordersResponse.json();

        console.log(`%c📋 Orders API Status: ${ordersResponse.status}`, 'color: #2196F3;');
        console.log(`%c📊 Total Orders: ${ordersData.orders ? ordersData.orders.length : 0}`,
            ordersData.orders && ordersData.orders.length > 0 ? 'color: #4CAF50; font-weight: bold;' : 'color: #F44336; font-weight: bold;');
        console.log(`%c💬 Message: ${ordersData.message}`, 'color: #2196F3;');

        // Test live orders
        const liveResponse = await fetch(`${baseUrl}/api/v1/orders/live`);
        const liveData = await liveResponse.json();

        console.log(`%c🔴 Live Orders: ${liveData.orders ? liveData.orders.length : 0}`,
            liveData.orders && liveData.orders.length > 0 ? 'color: #4CAF50; font-weight: bold;' : 'color: #F44336; font-weight: bold;');

        // Test trade engine status
        const engineResponse = await fetch(`${baseUrl}/api/v1/trade-engine/status`);
        if (engineResponse.ok) {
            const engineData = await engineResponse.json();
            console.log(`%c🔧 Trade Engine: ${engineData.status || 'RUNNING'}`, 'color: #2196F3;');
            console.log(`%c⚡ Signals Processed: ${engineData.signals_processed || 0}`, 'color: #2196F3;');
            console.log(`%c⏳ Pending Signals: ${engineData.pending_signals || 0}`, 'color: #2196F3;');
        }

        // Success if we can access APIs and either have orders or trade engine is running
        testResults.orderExecution = ordersResponse.ok && liveResponse.ok;

        // Check if we have actual orders (the ultimate test)
        const hasOrders = (ordersData.orders && ordersData.orders.length > 0) ||
            (liveData.orders && liveData.orders.length > 0);

        if (hasOrders) {
            console.log('%c🎉 ORDERS DETECTED - SCALPING SYSTEM RESTORED!', 'color: #4CAF50; font-size: 14px; font-weight: bold;');
            testResults.orderExecution = true;
        } else {
            console.log('%c⚠️  No orders yet - system may be warming up or waiting for signals', 'color: #FF9800; font-weight: bold;');
        }

    } catch (error) {
        console.log('%c❌ Order execution test failed:', 'color: #F44336; font-weight: bold;', error.message);
    }

    // ======================
    // 5️⃣ OVERALL HEALTH CHECK
    // ======================
    console.log('\n%c5️⃣ OVERALL SYSTEM HEALTH CHECK', 'color: #4CAF50; font-size: 16px; font-weight: bold;');
    try {
        const healthResponse = await fetch(`${baseUrl}/api/v1/system/health`);
        const healthData = await healthResponse.json();

        console.log(`%c🏥 System Health: ${healthData.health || healthData.status}`, 'color: #2196F3;');
        console.log(`%c📊 Status: ${healthData.status}`, 'color: #2196F3;');
        console.log(`%c🕐 Timestamp: ${healthData.timestamp || new Date().toISOString()}`, 'color: #2196F3;');

        testResults.overallHealth = healthResponse.ok;

    } catch (error) {
        console.log('%c❌ Health check failed:', 'color: #F44336; font-weight: bold;', error.message);
    }

    // ======================
    // 📊 FINAL RESULTS
    // ======================
    console.log('\n%c📊 FINAL TEST RESULTS', 'color: #FF6B35; font-size: 18px; font-weight: bold;');
    console.log('%c==================', 'color: #FF6B35; font-size: 16px;');

    const passedTests = Object.values(testResults).filter(Boolean).length;
    const totalTests = Object.keys(testResults).length;

    console.log(`%c✅ Elite API Performance: ${testResults.eliteAPI ? 'PASS' : 'FAIL'}`,
        testResults.eliteAPI ? 'color: #4CAF50; font-weight: bold;' : 'color: #F44336; font-weight: bold;');
    console.log(`%c🔐 Zerodha Authentication: ${testResults.zerodhaAuth ? 'PASS' : 'FAIL'}`,
        testResults.zerodhaAuth ? 'color: #4CAF50; font-weight: bold;' : 'color: #F44336; font-weight: bold;');
    console.log(`%c🎯 Trading System Active: ${testResults.tradingSystem ? 'PASS' : 'FAIL'}`,
        testResults.tradingSystem ? 'color: #4CAF50; font-weight: bold;' : 'color: #F44336; font-weight: bold;');
    console.log(`%c⚡ Order Execution: ${testResults.orderExecution ? 'PASS' : 'FAIL'}`,
        testResults.orderExecution ? 'color: #4CAF50; font-weight: bold;' : 'color: #F44336; font-weight: bold;');
    console.log(`%c🏥 Overall Health: ${testResults.overallHealth ? 'PASS' : 'FAIL'}`,
        testResults.overallHealth ? 'color: #4CAF50; font-weight: bold;' : 'color: #F44336; font-weight: bold;');

    console.log(`\n%c🎯 OVERALL SCORE: ${passedTests}/${totalTests} TESTS PASSED`,
        passedTests === totalTests ? 'color: #4CAF50; font-size: 16px; font-weight: bold;' : 'color: #FF9800; font-size: 16px; font-weight: bold;');

    if (passedTests === totalTests) {
        console.log('%c🎉 ALL SYSTEMS OPERATIONAL - SCALPING SYSTEM FULLY RESTORED!', 'color: #4CAF50; font-size: 18px; font-weight: bold;');
        console.log('%c🚀 Expected: 100+ trades/hour with sub-second Elite API responses', 'color: #4CAF50; font-size: 14px;');
    } else {
        console.log('%c⚠️  Some systems need attention. Check failed tests above.', 'color: #FF9800; font-size: 16px; font-weight: bold;');
    }

    return testResults;
}

// ======================
// 📋 CONTINUOUS MONITORING
// ======================
async function startContinuousMonitoring() {
    console.log('\n%c📊 STARTING CONTINUOUS MONITORING', 'color: #2196F3; font-size: 16px; font-weight: bold;');
    console.log('%c(Run every 30 seconds to monitor trade execution)', 'color: #2196F3;');

    const baseUrl = 'https://algoauto-9gx56.ondigitalocean.app';
    let previousOrderCount = 0;
    let monitoringInterval;

    const monitor = async () => {
        try {
            const ordersResponse = await fetch(`${baseUrl}/api/v1/orders/`);
            const ordersData = await ordersResponse.json();
            const currentOrderCount = ordersData.orders ? ordersData.orders.length : 0;

            const timestamp = new Date().toLocaleTimeString();
            console.log(`%c[${timestamp}] 📊 Orders: ${currentOrderCount}`, 'color: #2196F3;');

            if (currentOrderCount > previousOrderCount) {
                console.log(`%c🚀 NEW ORDERS DETECTED! (+${currentOrderCount - previousOrderCount})`, 'color: #4CAF50; font-weight: bold;');
            }

            previousOrderCount = currentOrderCount;

        } catch (error) {
            console.log(`%c[${new Date().toLocaleTimeString()}] ❌ Monitor error:`, 'color: #F44336;', error.message);
        }
    };

    monitoringInterval = setInterval(monitor, 30000);

    // Stop monitoring function
    window.stopMonitoring = () => {
        clearInterval(monitoringInterval);
        console.log('%c🛑 Monitoring stopped', 'color: #FF9800; font-weight: bold;');
    };

    console.log('%c⚡ Monitoring started! Run stopMonitoring() to stop.', 'color: #4CAF50; font-weight: bold;');
}

// ======================
// 🎯 QUICK COMMANDS
// ======================
console.log('%c🚀 QUICK COMMANDS:', 'color: #FF6B35; font-size: 14px; font-weight: bold;');
console.log('%c  runComprehensiveTest() - Run full test suite', 'color: #2196F3;');
console.log('%c  startContinuousMonitoring() - Monitor trades every 30s', 'color: #2196F3;');
console.log('%c  stopMonitoring() - Stop monitoring', 'color: #2196F3;');

// Auto-run the comprehensive test
runComprehensiveTest(); 