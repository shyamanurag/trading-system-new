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