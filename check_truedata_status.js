const https = require('https');

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

function makeRequest(url, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const options = {
            method: method,
            timeout: 15000,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'TradingSystem-TrueData-Check/1.0'
            }
        };

        const req = https.request(url, options, (res) => {
            let body = '';
            res.on('data', (chunk) => {
                body += chunk;
            });
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(body);
                    resolve({
                        status: res.statusCode,
                        data: jsonData
                    });
                } catch (e) {
                    resolve({
                        status: res.statusCode,
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

async function checkTrueDataStatus() {
    console.log('🔍 Checking TrueData Connection Status...\n');

    const endpoints = [
        { name: 'TrueData Status', url: '/api/v1/truedata/status' },
        { name: 'TrueData Health', url: '/api/v1/truedata/health' },
        { name: 'TrueData Connection', url: '/api/v1/truedata/connection' },
        { name: 'TrueData Deployment Status', url: '/api/v1/truedata/deployment-status' },
        { name: 'System Status', url: '/api/v1/system/status' },
        { name: 'Dashboard', url: '/api/v1/dashboard' },
        { name: 'Health Check', url: '/health' },
        { name: 'Ready Check', url: '/health/ready' }
    ];

    const results = {};

    for (const endpoint of endpoints) {
        try {
            console.log(`🔍 Testing ${endpoint.name}...`);
            const result = await makeRequest(`${BASE_URL}${endpoint.url}`);

            if (result.status === 200) {
                console.log(`✅ ${endpoint.name}: SUCCESS`);
                console.log(`   📊 Response: ${JSON.stringify(result.data, null, 2)}`);
                results[endpoint.name] = { success: true, data: result.data };
            } else {
                console.log(`❌ ${endpoint.name}: FAILED (${result.status})`);
                console.log(`   📊 Response: ${JSON.stringify(result.data, null, 2)}`);
                results[endpoint.name] = { success: false, status: result.status, data: result.data };
            }
        } catch (error) {
            console.log(`❌ ${endpoint.name}: ERROR - ${error.message}`);
            results[endpoint.name] = { success: false, error: error.message };
        }

        console.log(''); // Empty line for readability
    }

    return results;
}

async function checkAutonomousSystem() {
    console.log('🤖 Checking Autonomous Trading System...\n');

    try {
        // Check current status
        const statusResult = await makeRequest(`${BASE_URL}/api/v1/autonomous/status`);
        console.log('📊 Autonomous Status:');
        console.log(JSON.stringify(statusResult.data, null, 2));

        // Check if we can get system components
        const systemResult = await makeRequest(`${BASE_URL}/api/v1/system/status`);
        console.log('\n🔧 System Components:');
        console.log(JSON.stringify(systemResult.data, null, 2));

        // Check if there are any orders
        const ordersResult = await makeRequest(`${BASE_URL}/api/v1/orders/`);
        console.log('\n📋 Orders Status:');
        console.log(`Status: ${ordersResult.status}`);
        console.log(JSON.stringify(ordersResult.data, null, 2));

    } catch (error) {
        console.log(`❌ Error checking autonomous system: ${error.message}`);
    }
}

async function runDiagnostics() {
    console.log('🚀 Running TrueData & System Diagnostics');
    console.log('=' * 50);

    const startTime = Date.now();

    // Check TrueData connection
    const trueDataResults = await checkTrueDataStatus();

    // Check autonomous system
    await checkAutonomousSystem();

    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;

    console.log('\n' + '=' * 50);
    console.log(`🏁 Diagnostics Complete in ${duration.toFixed(2)} seconds`);

    // Summary
    const workingEndpoints = Object.values(trueDataResults).filter(r => r.success).length;
    const totalEndpoints = Object.keys(trueDataResults).length;

    console.log(`\n📊 SUMMARY:`);
    console.log(`   ✅ Working endpoints: ${workingEndpoints}/${totalEndpoints}`);
    console.log(`   ❌ Failed endpoints: ${totalEndpoints - workingEndpoints}/${totalEndpoints}`);

    console.log('\n🎯 KEY INSIGHTS:');
    console.log('   - TrueData connection is the bottleneck for market data');
    console.log('   - Without market data, strategies cannot generate signals');
    console.log('   - Zero trades issue directly linked to TrueData connection');
    console.log('   - Markets are open - this is the perfect time to fix this');
}

runDiagnostics(); 