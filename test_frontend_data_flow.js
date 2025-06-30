// 🔍 FRONTEND DATA FLOW VERIFICATION TEST
// Run this in your browser console to see what data is available

console.log('🚀 FRONTEND DATA FLOW TEST - Starting...');

// Function to test API endpoints
async function testEndpoint(url, name) {
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
            }
        });

        const data = await response.json();
        console.log(`✅ ${name}:`, {
            status: response.status,
            success: data.success,
            dataKeys: Object.keys(data),
            sampleData: data
        });

        return { name, status: response.status, data };
    } catch (error) {
        console.log(`❌ ${name}: ${error.message}`);
        return { name, error: error.message };
    }
}

// Test all key endpoints
async function runDataFlowTest() {
    console.log('\n📊 TESTING MAIN DATA SOURCES...');

    const endpoints = [
        { url: '/api/v1/autonomous/status', name: 'AUTONOMOUS STATUS (PRIMARY)' },
        { url: '/api/v1/dashboard/summary', name: 'DASHBOARD SUMMARY (FALLBACK)' },
        { url: '/api/v1/performance/daily-pnl', name: 'DAILY P&L' },
        { url: '/api/v1/recommendations/latest', name: 'RECOMMENDATIONS' },
        { url: '/api/v1/system/status', name: 'SYSTEM STATUS' },
        { url: '/api/v1/users', name: 'USERS' },
        { url: '/api/v1/broker/status', name: 'BROKER STATUS' }
    ];

    const results = await Promise.all(
        endpoints.map(ep => testEndpoint(ep.url, ep.name))
    );

    console.log('\n🎯 DATA AVAILABILITY SUMMARY:');
    results.forEach(result => {
        if (result.data) {
            const hasData = result.data.success &&
                (result.data.data || result.data.users || result.data.daily_pnl || result.data.recommendations);
            console.log(`${hasData ? '✅' : '⚠️'} ${result.name}: ${hasData ? 'HAS DATA' : 'EMPTY/NO DATA'}`);

            // Show key metrics for autonomous status
            if (result.name.includes('AUTONOMOUS') && result.data.data) {
                console.log(`   🔍 Key Metrics:`, {
                    active: result.data.data.is_active,
                    trades: result.data.data.total_trades,
                    pnl: result.data.data.daily_pnl,
                    positions: result.data.data.active_positions
                });
            }
        }
    });

    // Test what's currently in localStorage
    console.log('\n💾 FRONTEND STORAGE:');
    console.log('Auth Token:', localStorage.getItem('auth_token') ? 'Present' : 'Missing');
    console.log('User Info:', localStorage.getItem('user_info') ? JSON.parse(localStorage.getItem('user_info')) : 'Missing');

    // Test dashboard data processing
    console.log('\n🎭 DASHBOARD COMPONENT TEST:');
    console.log('Current URL:', window.location.href);
    console.log('React Components:', window.React ? 'Available' : 'Not Available');

    // Show what the main dashboard should be displaying
    const autonomousResult = results.find(r => r.name.includes('AUTONOMOUS'));
    if (autonomousResult && autonomousResult.data && autonomousResult.data.data) {
        const trading = autonomousResult.data.data;
        console.log('\n🎪 EXPECTED DASHBOARD DISPLAY:');
        console.log(`   Total P&L: ₹${(trading.daily_pnl || 0).toLocaleString()}`);
        console.log(`   Total Trades: ${trading.total_trades || 0}`);
        console.log(`   Success Rate: ${trading.success_rate || 70}%`);
        console.log(`   Active Users: ${trading.is_active ? 1 : 0}`);
        console.log(`   AUM: ₹100,000 (Paper Trading)`);
        console.log(`   Status: ${trading.is_active ? 'ACTIVE' : 'INACTIVE'}`);
    }

    return results;
}

// Run the test
runDataFlowTest().then(() => {
    console.log('\n🎉 FRONTEND DATA FLOW TEST COMPLETE!');
    console.log('\n💡 NEXT STEPS:');
    console.log('1. Check which endpoints have data vs empty');
    console.log('2. Verify your dashboard is using autonomous/status data');
    console.log('3. Check if other tabs need the same data fix');
    console.log('\n🔄 To rerun this test: runDataFlowTest()');
}).catch(error => {
    console.error('❌ Test failed:', error);
});

// Additional helper functions
window.testFrontendData = runDataFlowTest;

// Test specific dashboard component data
window.testDashboardData = function () {
    console.log('🎭 TESTING DASHBOARD COMPONENT DATA...');

    // Try to access React component state if possible
    const dashboardElements = document.querySelectorAll('[data-testid*="dashboard"], [class*="dashboard"], [class*="Dashboard"]');
    console.log('Dashboard elements found:', dashboardElements.length);

    // Check if data is being displayed
    const totalPnLElements = document.querySelectorAll('*');
    let displayedData = {};

    for (let element of totalPnLElements) {
        if (element.textContent && element.textContent.includes('₹')) {
            const text = element.textContent.trim();
            if (text.includes('₹') && text.length < 50) {
                displayedData[element.tagName] = text;
            }
        }
    }

    console.log('💰 DISPLAYED CURRENCY VALUES:', displayedData);

    // Check for trading status
    const statusElements = document.querySelectorAll('*');
    let statusData = [];

    for (let element of statusElements) {
        if (element.textContent) {
            const text = element.textContent.trim();
            if (text.includes('Active') || text.includes('ACTIVE') || text.includes('trades') || text.includes('Trading')) {
                if (text.length < 100) {
                    statusData.push(text);
                }
            }
        }
    }

    console.log('📊 DISPLAYED STATUS INFO:', [...new Set(statusData)].slice(0, 10));
};

console.log('\n🎯 AVAILABLE COMMANDS:');
console.log('testFrontendData() - Test all API endpoints');
console.log('testDashboardData() - Check what data is displayed');
console.log('\n▶️ Running initial test...'); 