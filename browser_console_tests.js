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

// Comprehensive Trading System Test Suite
// Tests singleton state persistence and signal generation pipeline

console.log("🚀 COMPREHENSIVE TRADING SYSTEM TEST SUITE");
console.log("Testing singleton fixes and signal generation pipeline...\n");

async function comprehensiveSystemTest() {
    const results = {
        singleton_test: null,
        signal_generation_test: null,
        trading_loop_test: null,
        market_data_format_test: null,
        overall_status: null
    };

    try {
        // Test 1: Singleton State Persistence (the original issue)
        console.log("1️⃣ TESTING SINGLETON STATE PERSISTENCE...");

        // Get initial state
        const initialStatus = await fetch('/api/v1/autonomous/status').then(r => r.json());
        console.log(`   Initial is_active: ${initialStatus.data.is_active}`);

        // Enable trading
        const enableResult = await fetch('/api/v1/autonomous/start', { method: 'POST' }).then(r => r.json());
        console.log(`   Enable result: ${enableResult.success}`);

        // Check state immediately 
        const immediateStatus = await fetch('/api/v1/autonomous/status').then(r => r.json());
        console.log(`   Immediate is_active: ${immediateStatus.data.is_active}`);

        // Wait a moment then check again (different request)
        await new Promise(resolve => setTimeout(resolve, 2000));
        const persistedStatus = await fetch('/api/v1/autonomous/status').then(r => r.json());
        console.log(`   Persisted is_active: ${persistedStatus.data.is_active}`);

        results.singleton_test = {
            passed: persistedStatus.data.is_active === true,
            details: {
                initial: initialStatus.data.is_active,
                immediate: immediateStatus.data.is_active,
                persisted: persistedStatus.data.is_active,
                session_id: persistedStatus.data.session_id
            }
        };

        if (results.singleton_test.passed) {
            console.log("   ✅ SINGLETON STATE PERSISTENCE: WORKING!");
        } else {
            console.log("   ❌ SINGLETON STATE PERSISTENCE: FAILED!");
        }

        // Test 2: Market Data Format (the data format fix)
        console.log("\n2️⃣ TESTING MARKET DATA FORMAT...");

        const marketDataTest = await fetch('/api/v1/debug/test-signal-generation').then(r => r.json());

        if (marketDataTest.success) {
            const sampleData = marketDataTest.data.market_data_sample;
            console.log(`   Symbols returned: ${sampleData.symbols_returned?.join(', ')}`);
            console.log(`   Price history type: ${sampleData.price_history_type}`);
            console.log(`   Price history length: ${sampleData.price_history_length}`);
            console.log(`   Sample data keys: ${sampleData.sample_data_keys?.join(', ')}`);

            results.market_data_format_test = {
                passed: sampleData.price_history_type === 'list' && sampleData.price_history_length > 0,
                details: sampleData
            };

            if (results.market_data_format_test.passed) {
                console.log("   ✅ MARKET DATA FORMAT: PROPER CANDLE DATA!");
            } else {
                console.log("   ❌ MARKET DATA FORMAT: STILL BROKEN!");
            }
        } else {
            console.log("   ❌ MARKET DATA FORMAT: TEST FAILED!");
            results.market_data_format_test = { passed: false, error: marketDataTest.error };
        }

        // Test 3: Signal Generation (the core issue)
        console.log("\n3️⃣ TESTING SIGNAL GENERATION...");

        if (marketDataTest.success) {
            const signalData = marketDataTest.data;
            console.log(`   Strategy engine exists: ${signalData.strategy_engine_exists}`);
            console.log(`   Market data exists: ${signalData.market_data_exists}`);
            console.log(`   Signals generated: ${signalData.signals_generated}`);
            console.log(`   Market open: ${signalData.market_open}`);
            console.log(`   Errors: ${signalData.errors.length}`);

            if (signalData.signals_generated > 0) {
                console.log("   📊 SIGNAL DETAILS:");
                signalData.signal_details.forEach((signal, i) => {
                    console.log(`      ${i + 1}. ${signal.symbol} ${signal.side} (Quality: ${signal.quality_score})`);
                });
            }

            if (signalData.errors.length > 0) {
                console.log("   ⚠️ ERRORS:");
                signalData.errors.forEach(error => console.log(`      - ${error}`));
            }

            results.signal_generation_test = {
                passed: signalData.signals_generated > 0,
                signals_count: signalData.signals_generated,
                details: {
                    strategy_engine: signalData.strategy_engine_exists,
                    market_data: signalData.market_data_exists,
                    market_open: signalData.market_open,
                    errors: signalData.errors,
                    signals: signalData.signal_details
                }
            };

            if (results.signal_generation_test.passed) {
                console.log(`   ✅ SIGNAL GENERATION: ${signalData.signals_generated} SIGNALS GENERATED!`);
            } else {
                console.log("   ❌ SIGNAL GENERATION: NO SIGNALS GENERATED!");
            }
        }

        // Test 4: Trading Loop Status
        console.log("\n4️⃣ TESTING TRADING LOOP STATUS...");

        const orchestratorStatus = await fetch('/api/v1/debug/orchestrator').then(r => r.json());

        if (orchestratorStatus.success) {
            const components = orchestratorStatus.data.component_status;
            console.log("   📊 COMPONENT STATUS:");
            Object.entries(components).forEach(([name, status]) => {
                const icon = status === 'SET' ? '✅' : '❌';
                console.log(`      ${icon} ${name}: ${status}`);
            });

            results.trading_loop_test = {
                passed: components.strategy_engine === 'SET' && components.market_data === 'SET',
                details: components
            };

            if (results.trading_loop_test.passed) {
                console.log("   ✅ TRADING LOOP: COMPONENTS READY!");
            } else {
                console.log("   ❌ TRADING LOOP: MISSING COMPONENTS!");
            }
        }

        // Overall Assessment
        console.log("\n🎯 OVERALL TEST RESULTS:");
        console.log("═══════════════════════════════");

        const tests = [
            { name: "Singleton State Persistence", result: results.singleton_test },
            { name: "Market Data Format", result: results.market_data_format_test },
            { name: "Signal Generation", result: results.signal_generation_test },
            { name: "Trading Loop Components", result: results.trading_loop_test }
        ];

        let passed = 0;
        tests.forEach(test => {
            const icon = test.result?.passed ? '✅' : '❌';
            const status = test.result?.passed ? 'PASS' : 'FAIL';
            console.log(`${icon} ${test.name}: ${status}`);
            if (test.result?.passed) passed++;
        });

        const score = `${passed}/${tests.length}`;
        console.log(`\n🏆 FINAL SCORE: ${score}`);

        if (passed === tests.length) {
            console.log("🎉 ALL SYSTEMS WORKING! AUTONOMOUS TRADING SHOULD BE FUNCTIONAL!");
            results.overall_status = "SUCCESS";
        } else if (passed >= 2) {
            console.log("⚠️ PARTIAL SUCCESS - SOME ISSUES REMAIN");
            results.overall_status = "PARTIAL";
        } else {
            console.log("❌ MAJOR ISSUES - NEEDS MORE DEBUGGING");
            results.overall_status = "FAILED";
        }

        // Special check for the original issue
        if (results.singleton_test?.passed && results.signal_generation_test?.passed) {
            console.log("\n🎯 CRITICAL SUCCESS: Both singleton persistence AND signal generation are working!");
            console.log("   This means autonomous trading should actually start generating and executing trades now!");
        }

        return results;

    } catch (error) {
        console.error("Test failed:", error);
        return { error: error.message, overall_status: "ERROR" };
    }
}

// Run the comprehensive test
comprehensiveSystemTest().then(results => {
    console.log("\n📋 TEST RESULTS SUMMARY:");
    console.log(JSON.stringify(results, null, 2));
});

// Also provide a simple quick test function
window.quickSignalTest = async function () {
    console.log("🔍 QUICK SIGNAL GENERATION TEST");
    const result = await fetch('/api/v1/debug/test-signal-generation').then(r => r.json());
    if (result.success) {
        console.log(`✅ Signals generated: ${result.data.signals_generated}`);
        console.log(`📊 Market data: ${result.data.market_data_exists ? 'Available' : 'Missing'}`);
        console.log(`🏭 Strategy engine: ${result.data.strategy_engine_exists ? 'Active' : 'Missing'}`);
        if (result.data.errors.length > 0) {
            console.log(`⚠️ Errors: ${result.data.errors.join(', ')}`);
        }
    } else {
        console.log(`❌ Test failed: ${result.error}`);
    }
};

console.log("\n💡 TIP: Run quickSignalTest() for a fast signal generation check!");

// 💰 === TRADE TRANSACTION FETCHING FUNCTIONS ===
// Copy this section to browser console to fetch today's trade data

const TRADE_API = {
    BASE_URL: 'https://algoauto-9gx56.ondigitalocean.app',
    
    // Helper function to make authenticated API calls
    async fetchWithAuth(endpoint, options = {}) {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        try {
            const response = await fetch(`${this.BASE_URL}${endpoint}`, {
                ...options,
                headers
            });
            
            const data = await response.json();
            return {
                success: response.ok,
                status: response.status,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    },

    // Fetch today's trade transactions from multiple endpoints
    async getTodaysTrades() {
        console.log(`%c🔍 Fetching Today's Trade Transactions...`, 'color: #2196F3; font-size: 16px; font-weight: bold');
        
        const today = new Date().toISOString().split('T')[0];
        console.log(`📅 Date Filter: ${today}`);
        
        const results = {};
        
        // 1. Try Dashboard Summary (Most comprehensive)
        console.log('%c1️⃣ Fetching Dashboard Summary...', 'color: #4CAF50; font-weight: bold');
        const dashboardResult = await this.fetchWithAuth('/api/v1/dashboard/dashboard/summary');
        if (dashboardResult.success) {
            results.dashboard = dashboardResult.data;
            console.log('%c✅ Dashboard Data:', 'color: #4CAF50', dashboardResult.data);
            
            // Extract trading metrics
            if (dashboardResult.data.autonomous_trading) {
                const trading = dashboardResult.data.autonomous_trading;
                console.log(`%c📊 Live Trading Status:
                🔥 Active: ${trading.is_active}
                📈 Total Trades: ${trading.total_trades}
                💰 Daily P&L: ₹${trading.daily_pnl}
                📍 Active Positions: ${trading.active_positions}
                🎯 Win Rate: ${trading.win_rate}%
                🕐 Session: ${trading.session_id || 'N/A'}`, 'color: #FF9800; font-weight: bold');
            }
        } else {
            console.error('❌ Dashboard fetch failed:', dashboardResult);
        }
        
        // 2. Try Performance Trades Endpoint
        console.log('%c2️⃣ Fetching Performance Trades...', 'color: #4CAF50; font-weight: bold');
        const performanceResult = await this.fetchWithAuth(`/api/v1/performance/trades?start_date=${today}&end_date=${today}`);
        if (performanceResult.success) {
            results.performance_trades = performanceResult.data;
            console.log('%c✅ Performance Trades:', 'color: #4CAF50', performanceResult.data);
            
            if (Array.isArray(performanceResult.data) && performanceResult.data.length > 0) {
                console.log(`%c📋 Trade Details:`, 'color: #9C27B0; font-weight: bold');
                performanceResult.data.forEach((trade, index) => {
                    console.log(`%c  ${index + 1}. ${trade.symbol} | ${trade.side} | Qty: ${trade.quantity} | Price: ₹${trade.price} | Time: ${trade.execution_time}`, 'color: #9C27B0');
                });
            }
        } else {
            console.error('❌ Performance trades fetch failed:', performanceResult);
        }
        
        // 3. Try General Trades Endpoint
        console.log('%c3️⃣ Fetching General Trades...', 'color: #4CAF50; font-weight: bold');
        const tradesResult = await this.fetchWithAuth('/api/v1/trades');
        if (tradesResult.success) {
            results.trades = tradesResult.data;
            console.log('%c✅ General Trades:', 'color: #4CAF50', tradesResult.data);
        } else {
            console.error('❌ General trades fetch failed:', tradesResult);
        }
        
        // 4. Try Live Trades Endpoint
        console.log('%c4️⃣ Fetching Live Trades...', 'color: #4CAF50; font-weight: bold');
        const liveTradesResult = await this.fetchWithAuth('/api/trades/live');
        if (liveTradesResult.success) {
            results.live_trades = liveTradesResult.data;
            console.log('%c✅ Live Trades:', 'color: #4CAF50', liveTradesResult.data);
        } else {
            console.error('❌ Live trades fetch failed:', liveTradesResult);
        }
        
        // 5. Try Trade Management Endpoint
        console.log('%c5️⃣ Fetching Trade Management Data...', 'color: #4CAF50; font-weight: bold');
        const tradeManagementResult = await this.fetchWithAuth('/api/v1/trade-management/');
        if (tradeManagementResult.success) {
            results.trade_management = tradeManagementResult.data;
            console.log('%c✅ Trade Management:', 'color: #4CAF50', tradeManagementResult.data);
        } else {
            console.error('❌ Trade management fetch failed:', tradeManagementResult);
        }
        
        // Summary Report
        console.log(`%c📊 === TODAY'S TRADING SUMMARY ===`, 'color: #E91E63; font-size: 18px; font-weight: bold; background: #FFF3E0; padding: 8px');
        
        let totalTrades = 0;
        let totalPnL = 0;
        let activePositions = 0;
        
        if (results.dashboard?.autonomous_trading) {
            const trading = results.dashboard.autonomous_trading;
            totalTrades = trading.total_trades || 0;
            totalPnL = trading.daily_pnl || 0;
            activePositions = trading.active_positions || 0;
        }
        
        console.log(`%c
        📅 Date: ${today}
        🎯 Total Trades: ${totalTrades}
        💰 Daily P&L: ₹${totalPnL.toFixed(2)}
        📍 Active Positions: ${activePositions}
        ⏰ Last Updated: ${new Date().toLocaleString()}
        `, 'color: #E91E63; font-size: 14px');
        
        return results;
    },

    // Fetch specific trade by ID
    async getTradeById(tradeId) {
        console.log(`%c🔍 Fetching Trade ID: ${tradeId}`, 'color: #2196F3; font-weight: bold');
        
        const result = await this.fetchWithAuth(`/api/v1/trades/${tradeId}`);
        if (result.success) {
            console.log('%c✅ Trade Details:', 'color: #4CAF50', result.data);
            return result.data;
        } else {
            console.error('❌ Trade fetch failed:', result);
            return null;
        }
    },

    // Fetch user-specific trades
    async getUserTrades(userId = 'AUTONOMOUS_TRADER') {
        console.log(`%c👤 Fetching Trades for User: ${userId}`, 'color: #2196F3; font-weight: bold');
        
        const result = await this.fetchWithAuth(`/api/v1/trades/users/${userId}`);
        if (result.success) {
            console.log('%c✅ User Trades:', 'color: #4CAF50', result.data);
            return result.data;
        } else {
            console.error('❌ User trades fetch failed:', result);
            return null;
        }
    },

    // Real-time trade monitoring
    async startTradeMonitoring(intervalSeconds = 30) {
        console.log(`%c🔄 Starting Real-time Trade Monitoring (${intervalSeconds}s intervals)`, 'color: #FF5722; font-weight: bold');
        
        const monitor = setInterval(async () => {
            console.log(`%c⏰ [${new Date().toLocaleTimeString()}] Updating trade data...`, 'color: #757575');
            await this.getTodaysTrades();
        }, intervalSeconds * 1000);
        
        console.log('%c✅ Monitoring started! Use TRADE_API.stopMonitoring() to stop.', 'color: #4CAF50');
        this.monitoringInterval = monitor;
        return monitor;
    },

    // Stop monitoring
    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
            console.log('%c🛑 Trade monitoring stopped.', 'color: #FF5722; font-weight: bold');
        }
    }
};

// Quick access functions
async function getTodaysTrades() {
    return await TRADE_API.getTodaysTrades();
}

async function getTradeById(id) {
    return await TRADE_API.getTradeById(id);
}

async function startTradeMonitoring(seconds = 30) {
    return await TRADE_API.startTradeMonitoring(seconds);
}

function stopTradeMonitoring() {
    TRADE_API.stopMonitoring();
}

// Auto-show instructions when this section is loaded
console.log(`%c
🚀 === TRADE TRANSACTION FETCHING READY ===

Quick Commands:
• getTodaysTrades()                    - Fetch all today's trades
• getTradeById('trade_id')            - Get specific trade details  
• startTradeMonitoring(30)            - Start real-time monitoring (30s)
• stopTradeMonitoring()               - Stop monitoring
• TRADE_API.getUserTrades('user_id')  - Get user-specific trades

Full API Object: TRADE_API.*

`, 'color: #4CAF50; font-size: 14px; font-weight: bold; background: #E8F5E8; padding: 10px'); 