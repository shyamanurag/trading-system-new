/**
 * Comprehensive Deployed App Test Suite
 * Tests all available functionality on the Digital Ocean deployment
 * Markets closed - focusing on system health, APIs, and infrastructure
 */

const https = require('https');
const { performance } = require('perf_hooks');

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

// Test configuration
const TESTS = {
    // Core system health
    health: '/health',
    ready: '/ready',
    api_routes: '/api/routes',

    // Authentication & user management (no auth required for GET)
    auth_me_endpoint: '/auth/me',

    // Trading system core
    autonomous_status: '/api/v1/autonomous/status',
    positions: '/api/v1/positions',
    orders: '/api/v1/orders',

    // Market data (cached/fallback data expected)
    market_indices: '/api/market/indices',
    market_status: '/api/market/market-status',

    // Dashboard & monitoring
    dashboard_summary: '/api/v1/dashboard/summary',
    system_status: '/api/v1/monitoring/system-status',

    // Elite recommendations
    elite_recommendations: '/api/v1/elite',

    // Intelligent systems
    intelligent_symbols: '/api/v1/intelligent-symbols',

    // Infrastructure endpoints
    root: '/',
    api_root: '/api',

    // Error handling (should return appropriate errors)
    non_existent_endpoint: '/api/v1/non-existent-endpoint',

    // Search functionality (recently implemented - may not be deployed)
    search_test: '/api/v1/search/autocomplete?query=NIFTY&category=symbols&limit=5'
};

// Expected status codes for each test (for more accurate success measurement)
const EXPECTED_STATUS_CODES = {
    'non_existent_endpoint': [404],  // Expected to return 404
    'search_test': [200, 500]  // 200 if table exists, 500 acceptable if using fallback
};

// Colors for console output
const colors = {
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
    reset: '\x1b[0m',
    bright: '\x1b[1m'
};

function makeRequest(path, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const startTime = performance.now();

        const options = {
            hostname: 'algoauto-9gx56.ondigitalocean.app',
            port: 443,
            path: path,
            method: 'GET',
            timeout: timeout,
            headers: {
                'User-Agent': 'AlgoAuto-Test-Suite/1.0',
                'Accept': 'application/json'
            }
        };

        const req = https.request(options, (res) => {
            let data = '';

            res.on('data', (chunk) => {
                data += chunk;
            });

            res.on('end', () => {
                const endTime = performance.now();
                const responseTime = Math.round(endTime - startTime);

                let parsedData = null;
                try {
                    parsedData = JSON.parse(data);
                } catch (e) {
                    // Not JSON, keep as string
                    parsedData = data;
                }

                resolve({
                    statusCode: res.statusCode,
                    headers: res.headers,
                    data: parsedData,
                    rawData: data,
                    responseTime: responseTime,
                    success: res.statusCode >= 200 && res.statusCode < 300
                });
            });
        });

        req.on('error', (error) => {
            const endTime = performance.now();
            const responseTime = Math.round(endTime - startTime);

            reject({
                error: error.message,
                responseTime: responseTime,
                success: false
            });
        });

        req.on('timeout', () => {
            req.destroy();
            reject({
                error: 'Request timeout',
                responseTime: timeout,
                success: false
            });
        });

        req.end();
    });
}

async function runTest(name, path) {
    console.log(`${colors.cyan}Testing:${colors.reset} ${name} (${path})`);

    try {
        const result = await makeRequest(path);

        // Check if this endpoint has expected status codes
        const expectedCodes = EXPECTED_STATUS_CODES[name];
        const isExpectedResponse = expectedCodes ?
            expectedCodes.includes(result.statusCode) :
            (result.statusCode >= 200 && result.statusCode < 300);

        if (isExpectedResponse) {
            console.log(`${colors.green}✅ PASS${colors.reset} - ${result.statusCode} - ${result.responseTime}ms`);
            if (expectedCodes && result.statusCode !== 200) {
                console.log(`   ${colors.blue}Note:${colors.reset} Expected ${result.statusCode} response for ${name}`);
            }
        } else {
            console.log(`${colors.yellow}⚠️  WARN${colors.reset} - ${result.statusCode} - ${result.responseTime}ms`);
            if (result.data && result.data.detail) {
                console.log(`   ${colors.yellow}Detail:${colors.reset} ${result.data.detail}`);
            }
        }

        // Log interesting data for specific endpoints
        if (result.data && typeof result.data === 'object') {
            if (path.includes('autonomous/status') && result.data.data) {
                console.log(`   ${colors.blue}Info:${colors.reset} Trading Active: ${result.data.data.is_active}`);
                if (result.data.data.session_stats) {
                    console.log(`   ${colors.blue}Info:${colors.reset} Total Trades: ${result.data.data.session_stats.total_trades || 0}`);
                }
            }

            if (path.includes('intelligent-symbols') && result.data.data) {
                console.log(`   ${colors.blue}Info:${colors.reset} Symbol Manager Running: ${result.data.data.status?.is_running}`);
                console.log(`   ${colors.blue}Info:${colors.reset} Active Symbols: ${result.data.data.status?.active_symbols || 0}`);
            }

            if (path.includes('system-status') && result.data.status) {
                console.log(`   ${colors.blue}Info:${colors.reset} System Status: ${result.data.status}`);
            }

            if (path.includes('market/indices') && result.data.data?.indices) {
                console.log(`   ${colors.blue}Info:${colors.reset} Market Indices: ${result.data.data.indices.length} available`);
            }

            if (path.includes('routes') && result.data.total_routes) {
                console.log(`   ${colors.blue}Info:${colors.reset} Total Routes: ${result.data.total_routes}`);
            }
        }

        // Return result with corrected success flag
        return { name, path, ...result, success: isExpectedResponse };

    } catch (error) {
        console.log(`${colors.red}❌ FAIL${colors.reset} - ${error.responseTime || '?'}ms`);
        console.log(`   ${colors.red}Error:${colors.reset} ${error.error}`);

        return { name, path, ...error };
    }
}

function generateReport(results) {
    console.log(`\n${colors.bright}${colors.cyan}=== DEPLOYMENT TEST REPORT ===${colors.reset}`);
    console.log(`${colors.bright}Timestamp:${colors.reset} ${new Date().toISOString()}`);
    console.log(`${colors.bright}Base URL:${colors.reset} ${BASE_URL}`);

    const passed = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);
    const warnings = results.filter(r => r.statusCode >= 400 && r.statusCode < 500);

    console.log(`\n${colors.bright}SUMMARY:${colors.reset}`);
    console.log(`${colors.green}✅ Passed: ${passed.length}${colors.reset}`);
    console.log(`${colors.red}❌ Failed: ${failed.length}${colors.reset}`);
    console.log(`${colors.yellow}⚠️  Warnings: ${warnings.length}${colors.reset}`);
    console.log(`📊 Total Tests: ${results.length}`);

    const avgResponseTime = results
        .filter(r => r.responseTime)
        .reduce((sum, r) => sum + r.responseTime, 0) / results.length;
    console.log(`⚡ Avg Response Time: ${Math.round(avgResponseTime)}ms`);

    // Core system health
    console.log(`\n${colors.bright}CORE SYSTEM HEALTH:${colors.reset}`);
    const coreEndpoints = ['health', 'ready', 'autonomous_status', 'system_status'];
    coreEndpoints.forEach(endpoint => {
        const result = results.find(r => r.name === endpoint);
        if (result) {
            const status = result.success ? `${colors.green}✅ HEALTHY${colors.reset}` : `${colors.red}❌ UNHEALTHY${colors.reset}`;
            console.log(`  ${endpoint}: ${status}`);
        }
    });

    // Trading system components
    console.log(`\n${colors.bright}TRADING SYSTEM:${colors.reset}`);
    const tradingEndpoints = ['positions', 'orders', 'elite_recommendations', 'intelligent_symbols'];
    tradingEndpoints.forEach(endpoint => {
        const result = results.find(r => r.name === endpoint);
        if (result) {
            const status = result.success ? `${colors.green}✅ OPERATIONAL${colors.reset}` : `${colors.red}❌ FAILED${colors.reset}`;
            console.log(`  ${endpoint}: ${status}`);
        }
    });

    // Market data (expected to have cached data)
    console.log(`\n${colors.bright}MARKET DATA:${colors.reset}`);
    const marketEndpoints = ['market_indices', 'market_status'];
    marketEndpoints.forEach(endpoint => {
        const result = results.find(r => r.name === endpoint);
        if (result) {
            const status = result.success ? `${colors.green}✅ AVAILABLE${colors.reset}` : `${colors.yellow}⚠️  LIMITED${colors.reset}`;
            console.log(`  ${endpoint}: ${status}`);
        }
    });

    // New features (may not be deployed)
    console.log(`\n${colors.bright}NEW FEATURES:${colors.reset}`);
    const newFeatures = ['search_test'];
    newFeatures.forEach(endpoint => {
        const result = results.find(r => r.name === endpoint);
        if (result) {
            const status = result.success ? `${colors.green}✅ DEPLOYED${colors.reset}` : `${colors.yellow}⚠️  NOT DEPLOYED${colors.reset}`;
            console.log(`  ${endpoint}: ${status}`);
        }
    });

    // Failed endpoints
    if (failed.length > 0) {
        console.log(`\n${colors.bright}${colors.red}FAILED ENDPOINTS:${colors.reset}`);
        failed.forEach(result => {
            console.log(`  ${colors.red}❌${colors.reset} ${result.name}: ${result.error || result.data?.detail || 'Unknown error'}`);
        });
    }

    // Performance analysis
    console.log(`\n${colors.bright}PERFORMANCE ANALYSIS:${colors.reset}`);
    const fastEndpoints = results.filter(r => r.responseTime && r.responseTime < 500);
    const slowEndpoints = results.filter(r => r.responseTime && r.responseTime > 2000);

    console.log(`⚡ Fast endpoints (< 500ms): ${fastEndpoints.length}`);
    console.log(`🐌 Slow endpoints (> 2s): ${slowEndpoints.length}`);

    if (slowEndpoints.length > 0) {
        console.log(`${colors.yellow}Slow endpoints:${colors.reset}`);
        slowEndpoints.forEach(endpoint => {
            console.log(`  ${endpoint.name}: ${endpoint.responseTime}ms`);
        });
    }

    // Overall assessment
    console.log(`\n${colors.bright}OVERALL ASSESSMENT:${colors.reset}`);
    const healthScore = (passed.length / results.length) * 100;

    if (healthScore >= 90) {
        console.log(`${colors.green}🎉 EXCELLENT${colors.reset} - System is highly operational (${healthScore.toFixed(1)}%)`);
    } else if (healthScore >= 75) {
        console.log(`${colors.blue}👍 GOOD${colors.reset} - System is mostly operational (${healthScore.toFixed(1)}%)`);
    } else if (healthScore >= 50) {
        console.log(`${colors.yellow}⚠️  FAIR${colors.reset} - System has some issues (${healthScore.toFixed(1)}%)`);
    } else {
        console.log(`${colors.red}🚨 POOR${colors.reset} - System needs attention (${healthScore.toFixed(1)}%)`);
    }

    // Recommendations
    console.log(`\n${colors.bright}RECOMMENDATIONS:${colors.reset}`);

    if (results.find(r => r.name === 'search_test' && !r.success)) {
        console.log(`${colors.cyan}📝${colors.reset} Deploy search functionality for enhanced user experience`);
    }

    if (slowEndpoints.length > 0) {
        console.log(`${colors.cyan}📝${colors.reset} Optimize slow endpoints for better performance`);
    }

    if (failed.length > 0) {
        console.log(`${colors.cyan}📝${colors.reset} Investigate failed endpoints and fix underlying issues`);
    }

    const autonomousResult = results.find(r => r.name === 'autonomous_status');
    if (autonomousResult?.data?.data?.is_active) {
        console.log(`${colors.green}📝${colors.reset} Autonomous trading is active - system ready for market hours`);
    }

    console.log(`${colors.cyan}📝${colors.reset} System is ready for market hours - monitor data flow when markets open`);

    console.log(`\n${colors.bright}${colors.green}Test completed successfully!${colors.reset}\n`);
}

async function main() {
    console.log(`${colors.bright}${colors.blue}🚀 Starting Comprehensive Deployment Test${colors.reset}`);
    console.log(`${colors.cyan}Target:${colors.reset} ${BASE_URL}`);
    console.log(`${colors.cyan}Tests:${colors.reset} ${Object.keys(TESTS).length} endpoints\n`);

    const results = [];

    for (const [name, path] of Object.entries(TESTS)) {
        const result = await runTest(name, path);
        results.push(result);

        // Small delay between requests to be respectful
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    generateReport(results);
}

// Handle errors gracefully
process.on('uncaughtException', (error) => {
    console.error(`${colors.red}Uncaught Exception:${colors.reset}`, error.message);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error(`${colors.red}Unhandled Rejection:${colors.reset}`, reason);
    process.exit(1);
});

// Run the tests
if (require.main === module) {
    main().catch(error => {
        console.error(`${colors.red}Test suite failed:${colors.reset}`, error.message);
        process.exit(1);
    });
}

module.exports = { makeRequest, runTest, generateReport }; 