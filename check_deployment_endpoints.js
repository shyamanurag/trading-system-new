const https = require('https');

const BASE_URL = 'https://trading-system-431204.el.r.appspot.com';

// Common endpoints to test
const endpoints = [
    '/',
    '/api',
    '/api/v1',
    '/api/v1/health',
    '/health',
    '/status',
    '/api/health',
    '/api/status',
    '/api/v1/system',
    '/api/v1/system/health',
    '/api/v1/market-data',
    '/api/v1/elite'
];

function testEndpoint(endpoint) {
    return new Promise((resolve) => {
        const url = `${BASE_URL}${endpoint}`;
        console.log(`Testing: ${url}`);

        const req = https.request(url, { timeout: 10000 }, (res) => {
            let body = '';
            res.on('data', (chunk) => {
                body += chunk;
            });
            res.on('end', () => {
                console.log(`${endpoint}: ${res.statusCode} - ${body.length} bytes`);
                if (res.statusCode !== 404) {
                    console.log(`✅ WORKING: ${endpoint} (${res.statusCode})`);
                    if (body.length < 500) {
                        console.log(`   Response: ${body}`);
                    }
                }
                resolve({ endpoint, status: res.statusCode, body });
            });
        });

        req.on('error', (error) => {
            console.log(`❌ ERROR: ${endpoint} - ${error.message}`);
            resolve({ endpoint, error: error.message });
        });

        req.on('timeout', () => {
            console.log(`⏰ TIMEOUT: ${endpoint}`);
            req.destroy();
            resolve({ endpoint, error: 'timeout' });
        });

        req.end();
    });
}

async function checkAllEndpoints() {
    console.log('🔍 Checking which endpoints are working...\n');

    const results = [];

    for (const endpoint of endpoints) {
        const result = await testEndpoint(endpoint);
        results.push(result);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second between requests
    }

    console.log('\n📊 SUMMARY:');
    const working = results.filter(r => r.status && r.status !== 404);
    const notFound = results.filter(r => r.status === 404);
    const errors = results.filter(r => r.error);

    console.log(`✅ Working endpoints: ${working.length}`);
    console.log(`❌ 404 Not Found: ${notFound.length}`);
    console.log(`🔥 Error endpoints: ${errors.length}`);

    if (working.length > 0) {
        console.log('\n🎯 WORKING ENDPOINTS:');
        working.forEach(r => console.log(`   ${r.endpoint} (${r.status})`));
    }

    return results;
}

checkAllEndpoints(); 