const https = require('https');
const http = require('http');

// Test configuration
const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';
const TEST_TIMEOUT = 30000; // 30 seconds

// Colors for console output
const colors = {
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    reset: '\x1b[0m',
    bold: '\x1b[1m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function makeRequest(url, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const isHttps = url.startsWith('https');
        const client = isHttps ? https : http;

        const options = {
            method: method,
            timeout: TEST_TIMEOUT,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'TradingSystem-Test/1.0'
            }
        };

        const req = client.request(url, options, (res) => {
            let body = '';
            res.on('data', (chunk) => {
                body += chunk;
            });
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(body);
                    resolve({
                        status: res.statusCode,
                        headers: res.headers,
                        data: jsonData
                    });
                } catch (e) {
                    resolve({
                        status: res.statusCode,
                        headers: res.headers,
                        data: body
                    });
                }
            });
        });

        req.on('error', (error) => {
            reject(error);
        });

        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });

        if (data) {
            req.write(JSON.stringify(data));
        }

        req.end();
    });
}

async function testEndpoint(name, endpoint, expectedStatus = 200) {
    try {
        log(`\n🔍 Testing ${name}...`, 'blue');
        const url = `${BASE_URL}${endpoint}`;
        const result = await makeRequest(url);

        if (result.status === expectedStatus) {
            log(`✅ ${name}: SUCCESS (${result.status})`, 'green');
            return { success: true, data: result.data };
        } else {
            log(`❌ ${name}: FAILED (${result.status})`, 'red');
            console.log('Response:', result.data);
            return { success: false, error: result.data };
        }
    } catch (error) {
        log(`❌ ${name}: ERROR - ${error.message}`, 'red');
        return { success: false, error: error.message };
    }
}

async function testLiveMarketData() {
    log('\n📊 Testing Live Market Data...', 'bold');

    const tests = [
        { name: 'Market Data Health', endpoint: '/api/v1/market-data/health' },
        { name: 'Live Market Data', endpoint: '/api/v1/market-data/live-data' },
        { name: 'NIFTY Data', endpoint: '/api/v1/market-data/NIFTY' },
        { name: 'BANKNIFTY Data', endpoint: '/api/v1/market-data/BANKNIFTY' },
        { name: 'Market Indices', endpoint: '/api/v1/market-data/indices' }
    ];

    const results = {};
    for (const test of tests) {
        const result = await testEndpoint(test.name, test.endpoint);
        results[test.name] = result;

        if (result.success && result.data) {
            if (test.name === 'Live Market Data' && Array.isArray(result.data)) {
                log(`   📈 Found ${result.data.length} symbols with live data`, 'yellow');
                if (result.data.length > 0) {
                    const sample = result.data[0];
                    log(`   🔍 Sample data: ${sample.symbol} - LTP: ${sample.ltp || 'N/A'}`, 'yellow');
                }
            }
        }
    }

    return results;
}

async function testTradingSystem() {
    log('\n🎯 Testing Trading System...', 'bold');

    const tests = [
        { name: 'System Health', endpoint: '/api/v1/system/health' },
        { name: 'System Status', endpoint: '/api/v1/system/status' },
        { name: 'Orchestrator Status', endpoint: '/api/v1/system/orchestrator/status' },
        { name: 'Strategy Status', endpoint: '/api/v1/strategies/status' },
        { name: 'Order Status', endpoint: '/api/v1/orders/status' },
        { name: 'Autonomous Trading Status', endpoint: '/api/v1/autonomous/status' }
    ];

    const results = {};
    for (const test of tests) {
        const result = await testEndpoint(test.name, test.endpoint);
        results[test.name] = result;

        if (result.success && result.data) {
            if (test.name === 'System Status') {
                log(`   🔧 Components: ${JSON.stringify(result.data.components || {}, null, 2)}`, 'yellow');
            }
            if (test.name === 'Strategy Status') {
                log(`   📊 Strategies: ${JSON.stringify(result.data.strategies || {}, null, 2)}`, 'yellow');
            }
            if (test.name === 'Order Status') {
                log(`   📋 Orders: ${JSON.stringify(result.data, null, 2)}`, 'yellow');
            }
        }
    }

    return results;
}

async function testEliteRecommendations() {
    log('\n🏆 Testing Elite Recommendations...', 'bold');

    const tests = [
        { name: 'Elite Recommendations', endpoint: '/api/v1/elite' },
        { name: 'Elite Status', endpoint: '/api/v1/elite/status' }
    ];

    const results = {};
    for (const test of tests) {
        const result = await testEndpoint(test.name, test.endpoint);
        results[test.name] = result;

        if (result.success && result.data) {
            if (test.name === 'Elite Recommendations' && Array.isArray(result.data)) {
                log(`   🎯 Found ${result.data.length} elite recommendations`, 'yellow');
                if (result.data.length > 0) {
                    const sample = result.data[0];
                    log(`   🔍 Sample: ${sample.symbol} - Confidence: ${sample.confidence || 'N/A'}%`, 'yellow');
                }
            }
        }
    }

    return results;
}

async function testOrderGeneration() {
    log('\n📝 Testing Order Generation...', 'bold');

    const tests = [
        { name: 'Recent Orders', endpoint: '/api/v1/orders/recent' },
        { name: 'Today Orders', endpoint: '/api/v1/orders/today' },
        { name: 'Trading Activity', endpoint: '/api/v1/trading/activity' }
    ];

    const results = {};
    for (const test of tests) {
        const result = await testEndpoint(test.name, test.endpoint);
        results[test.name] = result;

        if (result.success && result.data) {
            if (Array.isArray(result.data)) {
                log(`   📊 Found ${result.data.length} items`, 'yellow');
                if (result.data.length > 0) {
                    log(`   🔍 Latest: ${JSON.stringify(result.data[0], null, 2)}`, 'yellow');
                }
            } else if (typeof result.data === 'object') {
                log(`   📊 Activity: ${JSON.stringify(result.data, null, 2)}`, 'yellow');
            }
        }
    }

    return results;
}

async function testAutonomousTrading() {
    log('\n🤖 Testing Autonomous Trading Activation...', 'bold');

    try {
        // First check current status
        const statusResult = await testEndpoint('Current Autonomous Status', '/api/v1/autonomous/status');

        if (statusResult.success && statusResult.data) {
            const isActive = statusResult.data.is_active;
            log(`   🔍 Current Status: ${isActive ? 'ACTIVE' : 'INACTIVE'}`, isActive ? 'green' : 'red');

            if (!isActive) {
                log('\n   🚀 Attempting to activate autonomous trading...', 'yellow');
                const activateResult = await makeRequest(`${BASE_URL}/api/v1/autonomous/start`, 'POST');

                if (activateResult.status === 200) {
                    log('   ✅ Autonomous trading activation request sent', 'green');
                    log(`   📊 Response: ${JSON.stringify(activateResult.data, null, 2)}`, 'yellow');

                    // Wait 5 seconds and check status again
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    const newStatusResult = await testEndpoint('New Autonomous Status', '/api/v1/autonomous/status');

                    if (newStatusResult.success && newStatusResult.data) {
                        const newIsActive = newStatusResult.data.is_active;
                        log(`   🔍 New Status: ${newIsActive ? 'ACTIVE' : 'INACTIVE'}`, newIsActive ? 'green' : 'red');
                    }
                } else {
                    log(`   ❌ Activation failed: ${activateResult.status}`, 'red');
                    console.log('   Response:', activateResult.data);
                }
            }
        }
    } catch (error) {
        log(`   ❌ Error testing autonomous trading: ${error.message}`, 'red');
    }
}

async function runComprehensiveTest() {
    log('🚀 Starting Comprehensive Live Market Test', 'bold');
    log('=' * 50, 'blue');

    const startTime = Date.now();

    try {
        // Test all components
        const marketResults = await testLiveMarketData();
        const systemResults = await testTradingSystem();
        const eliteResults = await testEliteRecommendations();
        const orderResults = await testOrderGeneration();

        // Test autonomous trading
        await testAutonomousTrading();

        const endTime = Date.now();
        const duration = (endTime - startTime) / 1000;

        log('\n' + '=' * 50, 'blue');
        log(`🏁 Test Complete in ${duration.toFixed(2)} seconds`, 'bold');

        // Summary
        log('\n📊 SUMMARY:', 'bold');

        const allResults = { ...marketResults, ...systemResults, ...eliteResults, ...orderResults };
        const totalTests = Object.keys(allResults).length;
        const passedTests = Object.values(allResults).filter(r => r.success).length;
        const failedTests = totalTests - passedTests;

        log(`   ✅ Passed: ${passedTests}/${totalTests}`, 'green');
        log(`   ❌ Failed: ${failedTests}/${totalTests}`, failedTests > 0 ? 'red' : 'green');

        if (failedTests > 0) {
            log('\n❌ FAILED TESTS:', 'red');
            Object.entries(allResults).forEach(([name, result]) => {
                if (!result.success) {
                    log(`   - ${name}: ${result.error}`, 'red');
                }
            });
        }

        log('\n🎯 KEY INSIGHTS:', 'bold');
        log('   - Check if market data is flowing with real prices', 'yellow');
        log('   - Verify strategies are generating signals', 'yellow');
        log('   - Monitor order generation activity', 'yellow');
        log('   - Confirm autonomous trading is active', 'yellow');

    } catch (error) {
        log(`❌ Test failed with error: ${error.message}`, 'red');
    }
}

// Run the test
runComprehensiveTest(); 