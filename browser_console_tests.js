// 🧪 COMPREHENSIVE BROWSER CONSOLE TESTS FOR DEPLOYED APP
// Copy and paste this entire code into your browser console (F12)
// This will test all major endpoints and show what's working

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

// 🎨 Console styling functions
const log = {
    success: (msg) => console.log(`%c✅ ${msg}`, 'color: #28a745; font-weight: bold'),
    error: (msg) => console.log(`%c❌ ${msg}`, 'color: #dc3545; font-weight: bold'),
    info: (msg) => console.log(`%c💡 ${msg}`, 'color: #007bff; font-weight: bold'),
    warning: (msg) => console.log(`%c⚠️ ${msg}`, 'color: #ffc107; font-weight: bold'),
    data: (msg, data) => console.log(`%c📊 ${msg}`, 'color: #6f42c1; font-weight: bold', data)
};

// 🔧 Helper function for API calls
const testAPI = async (endpoint, method = 'GET', body = null) => {
    const url = `${BASE_URL}${endpoint}`;
    try {
        log.info(`Testing: ${method} ${endpoint}`);

        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };

        if (body) options.body = JSON.stringify(body);

        const response = await fetch(url, options);
        const data = await response.json();

        if (response.ok) {
            log.success(`${endpoint} - Status: ${response.status}`);
            return { success: true, status: response.status, data };
        } else {
            log.error(`${endpoint} - Status: ${response.status}`);
            return { success: false, status: response.status, data };
        }
    } catch (error) {
        log.error(`${endpoint} - Network Error: ${error.message}`);
        return { success: false, error: error.message };
    }
};

// 🧪 MAIN TEST SUITE
const runAllTests = async () => {
    console.clear();
    log.info('🚀 Starting Comprehensive API Tests...');
    console.log('='.repeat(60));

    const results = {
        passed: 0,
        failed: 0,
        total: 0,
        details: []
    };

    // 📍 TEST 1: Basic API Info
    log.info('TEST 1: Basic API Information');
    const apiInfo = await testAPI('/api');
    results.total++;
    if (apiInfo.success) {
        results.passed++;
        log.data('API Info:', apiInfo.data);
    } else {
        results.failed++;
    }
    console.log('-'.repeat(40));

    // 📍 TEST 2: Market Status (Critical)
    log.info('TEST 2: Market Status - CRITICAL ENDPOINT');
    const marketStatus = await testAPI('/api/market/market-status');
    results.total++;
    if (marketStatus.success) {
        results.passed++;
        const market = marketStatus.data.data;
        log.success(`Market: ${market.market_status} | Time: ${market.ist_time}`);
        log.data('TrueData Status:', market.data_provider);

        if (market.data_provider.status === 'CONNECTED') {
            log.success('✨ TrueData is CONNECTED - Live data available!');
        } else {
            log.warning('🔌 TrueData DISCONNECTED - Using fallback data');
        }
    } else {
        results.failed++;
    }
    console.log('-'.repeat(40));

    // 📍 TEST 3: Market Indices (Recently Fixed)
    log.info('TEST 3: Market Indices - RECENTLY FIXED');
    const indices = await testAPI('/api/market/indices');
    results.total++;
    if (indices.success) {
        results.passed++;
        const indicesData = indices.data.data.indices;
        log.success(`Found ${indicesData.length} indices`);

        indicesData.forEach(index => {
            const price = index.last_price || index.price;
            const volume = index.volume || 0;
            if (price > 0) {
                log.success(`📈 ${index.symbol}: ₹${price.toLocaleString()} | Vol: ${volume.toLocaleString()}`);
            } else {
                log.warning(`📊 ${index.symbol}: ₹0 (No live data - ${index.status})`);
            }
        });
    } else {
        results.failed++;
    }
    console.log('-'.repeat(40));

    // 📍 TEST 4: TrueData Connection Status
    log.info('TEST 4: TrueData Connection Status');
    const truedata = await testAPI('/api/v1/truedata/truedata/status');
    results.total++;
    if (truedata.success) {
        results.passed++;
        const td = truedata.data.data;
        log.data('TrueData Status:', {
            connected: td.connected,
            symbols: td.total_symbols,
            subscribed: td.subscribed_symbols
        });
    } else {
        results.failed++;
    }
    console.log('-'.repeat(40));

    // 📍 TEST 5: Authentication Status
    log.info('TEST 5: Zerodha Authentication Status');
    const auth = await testAPI('/auth/zerodha/status');
    results.total++;
    if (auth.success) {
        results.passed++;
        log.data('Auth Status:', auth.data);
    } else {
        results.failed++;
        log.warning('Auth endpoint may be deploying...');
    }
    console.log('-'.repeat(40));

    // 📍 TEST 6: Available Routes
    log.info('TEST 6: Available API Routes');
    const routes = await testAPI('/api/routes');
    results.total++;
    if (routes.success) {
        results.passed++;
        log.data('Available Routes:', routes.data);
    } else {
        results.failed++;
    }
    console.log('-'.repeat(40));

    // 📍 TEST 7: Symbol Subscription Test
    log.info('TEST 7: Symbol Subscription Test');
    const symbols = ['NIFTY-I', 'BANKNIFTY-I'];
    const subscription = await testAPI('/api/v1/truedata/truedata/subscribe', 'POST', symbols);
    results.total++;
    if (subscription.success) {
        results.passed++;
        log.success('Symbol subscription successful');
        log.data('Subscription Result:', subscription.data);
    } else {
        results.failed++;
        log.error('Symbol subscription failed');
    }
    console.log('-'.repeat(40));

    // 📍 TEST 8: Autonomous Trading Status
    log.info('TEST 8: Autonomous Trading Status');
    const autonomous = await testAPI('/api/v1/autonomous/status');
    results.total++;
    if (autonomous.success) {
        results.passed++;
        log.data('Autonomous Status:', autonomous.data);
    } else {
        results.failed++;
    }
    console.log('-'.repeat(40));

    // 📍 FINAL RESULTS
    console.log('='.repeat(60));
    log.info('🏁 TEST RESULTS SUMMARY');
    console.log('='.repeat(60));

    const passRate = Math.round((results.passed / results.total) * 100);

    if (passRate >= 80) {
        log.success(`✨ EXCELLENT: ${results.passed}/${results.total} tests passed (${passRate}%)`);
    } else if (passRate >= 60) {
        log.warning(`⚠️ GOOD: ${results.passed}/${results.total} tests passed (${passRate}%)`);
    } else {
        log.error(`❌ NEEDS WORK: ${results.passed}/${results.total} tests passed (${passRate}%)`);
    }

    // 💡 Recommendations based on results
    console.log('='.repeat(60));
    log.info('💡 RECOMMENDATIONS FOR YOUR SYSTEM:');
    console.log('='.repeat(60));

    if (marketStatus.success) {
        log.success('✅ Market Status API is working perfectly');
    }

    if (indices.success) {
        log.success('✅ Market Indices API is working (recently fixed)');
        if (indices.data.data.indices.every(i => i.last_price === 0)) {
            log.warning('💡 TrueData connection needed for live prices');
        }
    }

    log.info('🔧 Next Steps:');
    console.log('1. Fix TrueData connection for live data');
    console.log('2. Set up daily Zerodha authentication');
    console.log('3. Test autonomous trading during market hours');
    console.log('4. Monitor system during live trading session');

    return results;
};

// 🎯 SPECIFIC SYMBOL TESTS
const testSpecificSymbols = async () => {
    log.info('🎯 Testing Specific Symbols...');

    const testSymbols = [
        'NIFTY-I',
        'BANKNIFTY-I',
        'RELIANCE',
        'TCS',
        'HDFC',
        'INFY'
    ];

    for (const symbol of testSymbols) {
        try {
            // Try to get individual symbol data
            const result = await testAPI(`/api/v1/market/symbol/${symbol}`);
            if (result.success) {
                log.success(`${symbol}: Data available`);
                log.data(`${symbol} Data:`, result.data);
            } else {
                log.warning(`${symbol}: No data or endpoint not available`);
            }
        } catch (error) {
            log.error(`${symbol}: Error - ${error.message}`);
        }
    }
};

// 🚀 QUICK HEALTH CHECK
const quickHealthCheck = async () => {
    log.info('⚡ Quick Health Check...');

    const criticalEndpoints = [
        '/api',
        '/api/market/market-status',
        '/api/market/indices'
    ];

    let healthy = 0;

    for (const endpoint of criticalEndpoints) {
        const result = await testAPI(endpoint);
        if (result.success) {
            healthy++;
            log.success(`${endpoint} ✅`);
        } else {
            log.error(`${endpoint} ❌`);
        }
    }

    const healthScore = Math.round((healthy / criticalEndpoints.length) * 100);

    if (healthScore === 100) {
        log.success(`🎉 SYSTEM HEALTHY: ${healthy}/${criticalEndpoints.length} critical endpoints working`);
    } else {
        log.warning(`⚠️ SYSTEM DEGRADED: ${healthy}/${criticalEndpoints.length} critical endpoints working`);
    }

    return healthScore;
};

// 📊 REAL-TIME DATA MONITOR
const monitorRealTimeData = async (duration = 30) => {
    log.info(`📊 Monitoring real-time data for ${duration} seconds...`);

    let updates = 0;
    const interval = setInterval(async () => {
        const indices = await testAPI('/api/market/indices');
        if (indices.success) {
            const nifty = indices.data.data.indices.find(i => i.symbol === 'NIFTY');
            const banknifty = indices.data.data.indices.find(i => i.symbol === 'BANKNIFTY');

            console.log(`📈 Live Update ${++updates}:`, {
                time: new Date().toLocaleTimeString(),
                nifty: nifty?.last_price || 0,
                banknifty: banknifty?.last_price || 0,
                truedata_status: indices.data.data.truedata_connection?.connection_healthy
            });
        }
    }, 5000);

    setTimeout(() => {
        clearInterval(interval);
        log.success(`✅ Monitoring complete. Total updates: ${updates}`);
    }, duration * 1000);
};

// 🎮 INTERACTIVE FUNCTIONS
console.log(`
%c🧪 COMPREHENSIVE TESTING SUITE LOADED! 🧪
%c
Available Commands:
• runAllTests()        - Run comprehensive test suite
• quickHealthCheck()   - Quick system health check  
• testSpecificSymbols() - Test individual symbols
• monitorRealTimeData(30) - Monitor live data for 30 seconds

%c🚀 Quick Start: Type runAllTests() and press Enter
`,
    'color: #28a745; font-size: 18px; font-weight: bold',
    'color: #007bff; font-size: 14px',
    'color: #dc3545; font-size: 14px; font-weight: bold'
);

// AUTONOMOUS TRADING BROWSER CONSOLE SCRIPT
// Copy and paste this entire script into your browser console on the trading app page

console.log("🚀 AUTONOMOUS TRADING CONSOLE CONTROLLER");
console.log("=" * 50);

const API_BASE = 'https://algoauto-9gx56.ondigitalocean.app/api/v1';

// Helper function for API calls
async function apiCall(endpoint, method = 'GET', data = null) {
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        const result = await response.json();
        return {
            status: response.status,
            success: response.ok,
            data: result
        };
    } catch (error) {
        return {
            status: 0,
            success: false,
            error: error.message
        };
    }
}

// 1. Check Current Trading Status
async function checkTradingStatus() {
    console.log("\n📊 CHECKING CURRENT TRADING STATUS");
    console.log("-".repeat(40));

    const result = await apiCall('/autonomous/status');

    if (result.success) {
        const data = result.data.data || result.data;
        console.log(`✅ Status Check Success`);
        console.log(`🤖 Trading Active: ${data.is_active}`);
        console.log(`🆔 Session ID: ${data.session_id}`);
        console.log(`⏰ Start Time: ${data.start_time}`);
        console.log(`💚 Last Heartbeat: ${data.last_heartbeat}`);
        console.log(`📈 Active Strategies: ${data.active_strategies?.length || 0}`);
        console.log(`📊 Active Positions: ${data.active_positions?.length || 0}`);
        console.log(`💰 Daily P&L: ${data.daily_pnl}`);

        return data.is_active;
    } else {
        console.log(`❌ Status Check Failed: ${result.status}`);
        console.log(`Error: ${JSON.stringify(result.data, null, 2)}`);
        return false;
    }
}

// 2. Start Autonomous Trading (Multiple Methods)
async function startAutonomousTrading() {
    console.log("\n🚀 ATTEMPTING TO START AUTONOMOUS TRADING");
    console.log("-".repeat(45));

    // Method 1: Standard start endpoint
    console.log("Method 1: Standard Start Endpoint");
    let result = await apiCall('/autonomous/start', 'POST');

    if (result.success) {
        console.log("✅ SUCCESS! Autonomous trading started");
        console.log(`Response: ${JSON.stringify(result.data, null, 2)}`);
        return true;
    } else {
        console.log(`❌ Method 1 Failed: ${result.status}`);
        console.log(`Error: ${JSON.stringify(result.data, null, 2)}`);
    }

    // Method 2: Try trading control endpoint
    console.log("\nMethod 2: Trading Control Endpoint");
    result = await apiCall('/trading/control/autonomous/start', 'POST');

    if (result.success) {
        console.log("✅ SUCCESS! Trading started via control endpoint");
        return true;
    } else {
        console.log(`❌ Method 2 Failed: ${result.status}`);
    }

    // Method 3: Try direct enable
    console.log("\nMethod 3: Direct Enable");
    result = await apiCall('/autonomous/enable', 'POST');

    if (result.success) {
        console.log("✅ SUCCESS! Trading enabled");
        return true;
    } else {
        console.log(`❌ Method 3 Failed: ${result.status}`);
    }

    console.log("\n❌ All start methods failed!");
    return false;
}

// 3. Force Initialize System (if needed)
async function forceInitializeSystem() {
    console.log("\n🔧 ATTEMPTING FORCE SYSTEM INITIALIZATION");
    console.log("-".repeat(45));

    // Try to initialize components individually
    const endpoints = [
        '/system/initialize',
        '/autonomous/initialize',
        '/trading/initialize',
        '/system/health-check'
    ];

    for (const endpoint of endpoints) {
        console.log(`Trying: ${endpoint}`);
        const result = await apiCall(endpoint, 'POST');

        if (result.success) {
            console.log(`✅ Success: ${endpoint}`);
            console.log(`Response: ${JSON.stringify(result.data, null, 2)}`);
        } else {
            console.log(`❌ Failed: ${endpoint} - ${result.status}`);
        }
    }
}

// 4. Check Market Status
async function checkMarketStatus() {
    console.log("\n📈 CHECKING MARKET STATUS");
    console.log("-".repeat(30));

    const result = await apiCall('/market/market-status');

    if (result.success) {
        const data = result.data;
        console.log(`✅ Market Status: ${data.status}`);
        console.log(`🕐 Current Time: ${data.current_time}`);
        console.log(`📊 Trading Hours: ${data.is_trading_hours}`);
        console.log(`📅 Trading Day: ${data.is_trading_day}`);
        return data.status === 'OPEN';
    } else {
        console.log(`❌ Market Status Check Failed: ${result.status}`);
        return false;
    }
}

// 5. Monitor Trading (Run continuously)
function startTradingMonitor() {
    console.log("\n👁️ STARTING TRADING MONITOR");
    console.log("-".repeat(30));
    console.log("Monitoring every 30 seconds...");

    const monitor = setInterval(async () => {
        const status = await checkTradingStatus();

        if (status) {
            console.log(`✅ ${new Date().toLocaleTimeString()} - Trading is ACTIVE`);
        } else {
            console.log(`⚠️ ${new Date().toLocaleTimeString()} - Trading is INACTIVE`);
        }
    }, 30000);

    // Save monitor reference globally so user can stop it
    window.tradingMonitor = monitor;
    console.log("💡 To stop monitoring, run: clearInterval(window.tradingMonitor)");

    return monitor;
}

// 6. Emergency Trading Stop
async function emergencyStop() {
    console.log("\n🛑 EMERGENCY STOP AUTONOMOUS TRADING");
    console.log("-".repeat(40));

    const result = await apiCall('/autonomous/stop', 'POST');

    if (result.success) {
        console.log("✅ Emergency stop successful");
        if (window.tradingMonitor) {
            clearInterval(window.tradingMonitor);
            console.log("🛑 Monitor stopped");
        }
    } else {
        console.log(`❌ Emergency stop failed: ${result.status}`);
    }
}

// 7. Complete Trading Setup (All-in-one)
async function completeTradingSetup() {
    console.log("\n🎯 COMPLETE AUTONOMOUS TRADING SETUP");
    console.log("=".repeat(50));

    // Step 1: Check market status
    const marketOpen = await checkMarketStatus();
    if (!marketOpen) {
        console.log("⚠️ Warning: Market appears to be closed");
    }

    // Step 2: Check current status
    const isActive = await checkTradingStatus();

    if (isActive) {
        console.log("✅ Trading is already active!");
        startTradingMonitor();
        return true;
    }

    // Step 3: Try to start trading
    const started = await startAutonomousTrading();

    if (!started) {
        console.log("🔧 Trying force initialization...");
        await forceInitializeSystem();

        // Try starting again after initialization
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
        const retryStarted = await startAutonomousTrading();

        if (retryStarted) {
            console.log("✅ Trading started after force initialization!");
        } else {
            console.log("❌ Failed to start trading even after initialization");
            return false;
        }
    }

    // Step 4: Start monitoring
    console.log("\n🎉 TRADING SETUP COMPLETE!");
    console.log("Starting continuous monitoring...");
    startTradingMonitor();

    return true;
}

// 8. Quick Status Dashboard
async function quickDashboard() {
    console.log("\n📊 QUICK TRADING DASHBOARD");
    console.log("=".repeat(40));

    // Get multiple status checks in parallel
    const [tradingStatus, marketStatus] = await Promise.all([
        apiCall('/autonomous/status'),
        apiCall('/market/market-status')
    ]);

    // Trading Status
    if (tradingStatus.success) {
        const data = tradingStatus.data.data || tradingStatus.data;
        console.log(`🤖 Trading: ${data.is_active ? '🟢 ACTIVE' : '🔴 INACTIVE'}`);
        console.log(`💰 Daily P&L: ${data.daily_pnl || 0}`);
        console.log(`📊 Positions: ${data.active_positions?.length || 0}`);
    }

    // Market Status
    if (marketStatus.success) {
        const data = marketStatus.data;
        console.log(`📈 Market: ${data.status === 'OPEN' ? '🟢 OPEN' : '🔴 CLOSED'}`);
        console.log(`🕐 Time: ${data.current_time || 'Unknown'}`);
    }

    console.log("\n💡 Available Commands:");
    console.log("  completeTradingSetup() - Full setup and start");
    console.log("  startAutonomousTrading() - Just start trading");
    console.log("  checkTradingStatus() - Check status");
    console.log("  startTradingMonitor() - Start monitoring");
    console.log("  emergencyStop() - Emergency stop");
    console.log("  quickDashboard() - This dashboard");
}

// Make functions globally available
window.completeTradingSetup = completeTradingSetup;
window.startAutonomousTrading = startAutonomousTrading;
window.checkTradingStatus = checkTradingStatus;
window.startTradingMonitor = startTradingMonitor;
window.emergencyStop = emergencyStop;
window.quickDashboard = quickDashboard;
window.forceInitializeSystem = forceInitializeSystem;

// Auto-run dashboard
setTimeout(quickDashboard, 1000);

console.log("\n🎯 AUTONOMOUS TRADING CONSOLE READY!");
console.log("Type 'completeTradingSetup()' to start everything!");
console.log("Or type 'quickDashboard()' to see status"); 