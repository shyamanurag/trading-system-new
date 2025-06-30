// 🎯 COMPREHENSIVE FRONTEND FIXES VERIFICATION
// Run this in your browser console to test all tab fixes

console.log('🚀 TESTING ALL FRONTEND FIXES...');

// Test function for autonomous status endpoint
async function testAutonomousEndpoint() {
    console.log('\n🔍 TESTING AUTONOMOUS STATUS ENDPOINT...');
    try {
        const response = await fetch('/api/v1/autonomous/status');
        const data = await response.json();

        if (data.success && data.data) {
            console.log('✅ Autonomous endpoint working!');
            console.log('📊 Real trading data:', {
                trades: data.data.total_trades,
                pnl: `₹${(data.data.daily_pnl || 0).toLocaleString()}`,
                active: data.data.is_active,
                success_rate: `${data.data.success_rate || 0}%`
            });
            return data.data;
        } else {
            console.log('⚠️ Autonomous endpoint returns no data');
            return null;
        }
    } catch (error) {
        console.log('❌ Autonomous endpoint error:', error.message);
        return null;
    }
}

// Test all dashboard tab APIs
async function testDashboardAPIs() {
    console.log('\n🔍 TESTING DASHBOARD API ENDPOINTS...');

    const endpoints = [
        { name: 'Dashboard Summary', url: '/api/v1/dashboard/summary' },
        { name: 'Daily P&L', url: '/api/v1/performance/daily-pnl' },
        { name: 'Recommendations', url: '/api/v1/recommendations/latest' },
        { name: 'Users', url: '/api/v1/users' },
        { name: 'Broker Users', url: '/api/v1/broker/users' },
        { name: 'System Status', url: '/api/v1/system/status' },
        { name: 'Broker Status', url: '/api/v1/broker/status' }
    ];

    const results = {};

    for (const endpoint of endpoints) {
        try {
            const response = await fetch(endpoint.url);
            const data = await response.json();
            const hasData = data.success && (
                data.data || data.users || data.daily_pnl ||
                data.recommendations || data.system_metrics
            );

            results[endpoint.name] = {
                status: response.status,
                hasData: hasData,
                dataKeys: Object.keys(data)
            };

            console.log(`${hasData ? '✅' : '⚠️'} ${endpoint.name}: ${hasData ? 'HAS DATA' : 'EMPTY'}`);
        } catch (error) {
            results[endpoint.name] = { error: error.message };
            console.log(`❌ ${endpoint.name}: ${error.message}`);
        }
    }

    return results;
}

// Test Today's Trades fix
async function testTodaysTradesFix() {
    console.log('\n🔍 TESTING TODAY\'S TRADES FIX...');

    // Test the old broken endpoint
    try {
        const oldResponse = await fetch('/api/v1/dashboard/dashboard/summary');
        console.log('🚫 Old broken endpoint still accessible (should be fixed in component)');
    } catch (error) {
        console.log('✅ Old broken endpoint properly handled');
    }

    // Test the correct endpoint
    try {
        const newResponse = await fetch('/api/v1/autonomous/status');
        const data = await newResponse.json();

        if (data.success && data.data && data.data.total_trades > 0) {
            console.log('✅ Today\'s Trades fix working! Real data available:');
            console.log(`   📊 ${data.data.total_trades} trades, ₹${(data.data.daily_pnl || 0).toLocaleString()} P&L`);
            return true;
        } else {
            console.log('⚠️ Today\'s Trades endpoint fixed but no trading data');
            return false;
        }
    } catch (error) {
        console.log('❌ Today\'s Trades fix failed:', error.message);
        return false;
    }
}

// Test component data prop passing
function testComponentProps() {
    console.log('\n🔍 TESTING COMPONENT PROP PASSING...');

    // Check if React DevTools is available
    if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
        console.log('✅ React DevTools detected - you can inspect component props');
        console.log('💡 Look for these components with tradingData props:');
        console.log('   - EliteRecommendationsDashboard');
        console.log('   - UserPerformanceDashboard');
        console.log('   - AutonomousTradingDashboard');
        console.log('   - UserManagementDashboard');
        console.log('   - TodaysTradeReport');
    } else {
        console.log('⚠️ React DevTools not detected - install for component inspection');
    }

    // Check for dashboard elements
    const dashboardElements = document.querySelectorAll('[class*="Dashboard"], [class*="dashboard"]');
    console.log(`📊 Found ${dashboardElements.length} dashboard elements in DOM`);

    return dashboardElements.length > 0;
}

// Test displayed data vs API data consistency
async function testDataConsistency() {
    console.log('\n🔍 TESTING DATA CONSISTENCY...');

    const autonomousData = await testAutonomousEndpoint();

    if (!autonomousData) {
        console.log('⚠️ No autonomous data to test consistency');
        return false;
    }

    // Look for displayed values in DOM
    const currencyElements = Array.from(document.querySelectorAll('*')).filter(el =>
        el.textContent && el.textContent.includes('₹') && el.textContent.length < 50
    );

    const tradeElements = Array.from(document.querySelectorAll('*')).filter(el =>
        el.textContent && el.textContent.includes('trade') && el.textContent.length < 100
    );

    console.log(`💰 Found ${currencyElements.length} currency displays in UI`);
    console.log(`📊 Found ${tradeElements.length} trade-related displays in UI`);

    // Check if real data values appear in UI
    const realPnL = autonomousData.daily_pnl || 0;
    const realTrades = autonomousData.total_trades || 0;

    const pnlDisplayed = currencyElements.some(el =>
        el.textContent.includes(realPnL.toLocaleString())
    );

    const tradesDisplayed = tradeElements.some(el =>
        el.textContent.includes(realTrades.toString())
    );

    console.log(`${pnlDisplayed ? '✅' : '❌'} Real P&L (₹${realPnL.toLocaleString()}) displayed in UI`);
    console.log(`${tradesDisplayed ? '✅' : '❌'} Real trades (${realTrades}) displayed in UI`);

    return pnlDisplayed && tradesDisplayed;
}

// Test empty page fixes
function testEmptyPageFixes() {
    console.log('\n🔍 TESTING EMPTY PAGE FIXES...');

    const emptyIndicators = [
        'No data available',
        'coming soon',
        'No performance data',
        'No users found',
        'No trades to display'
    ];

    const pageText = document.body.textContent.toLowerCase();
    const emptyCount = emptyIndicators.reduce((count, indicator) => {
        return count + (pageText.includes(indicator.toLowerCase()) ? 1 : 0);
    }, 0);

    console.log(`📋 Empty page indicators found: ${emptyCount}`);

    if (emptyCount === 0) {
        console.log('✅ No empty page indicators - all tabs should have content!');
        return true;
    } else {
        console.log('⚠️ Some pages may still be empty - check individual tabs');
        return false;
    }
}

// Main test runner
async function runAllTests() {
    console.log('🎯 COMPREHENSIVE FRONTEND FIXES TEST');
    console.log('=====================================');

    const results = {
        autonomousEndpoint: await testAutonomousEndpoint(),
        dashboardAPIs: await testDashboardAPIs(),
        todaysTradesFix: await testTodaysTradesFix(),
        componentProps: testComponentProps(),
        dataConsistency: await testDataConsistency(),
        emptyPageFixes: testEmptyPageFixes()
    };

    console.log('\n📊 TEST RESULTS SUMMARY:');
    console.log('========================');

    Object.entries(results).forEach(([test, result]) => {
        const status = typeof result === 'boolean' ? (result ? '✅ PASS' : '❌ FAIL') : '📊 DATA';
        console.log(`${status} ${test}`);
    });

    console.log('\n💡 NEXT STEPS:');
    console.log('===============');

    if (results.autonomousEndpoint && results.autonomousEndpoint.total_trades > 0) {
        console.log('✅ Your autonomous trading system has real data!');
        console.log('🎯 All frontend fixes should now show your real trading performance');
        console.log('📊 Navigate through all tabs to see populated data');
    } else {
        console.log('⚠️ No autonomous trading data detected');
        console.log('🔧 Start autonomous trading to see full frontend functionality');
        console.log('📱 Use: window.startTrading() in console or dashboard controls');
    }

    console.log('\n🔄 To rerun tests: runAllTests()');

    return results;
}

// Helper function to start trading (if available)
window.startTrading = async function () {
    console.log('🚀 Attempting to start autonomous trading...');
    try {
        const response = await fetch('/api/v1/broker/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'start', paper_trading: true })
        });

        const data = await response.json();
        if (data.success) {
            console.log('✅ Trading started successfully!');
            console.log('⏳ Wait 30 seconds, then run: runAllTests()');
        } else {
            console.log('❌ Failed to start trading:', data.message);
        }
    } catch (error) {
        console.log('❌ Error starting trading:', error.message);
    }
};

// Make test function globally available
window.runAllTests = runAllTests;
window.testAutonomousEndpoint = testAutonomousEndpoint;

// Auto-run tests
console.log('▶️ Running tests automatically...');
runAllTests(); 