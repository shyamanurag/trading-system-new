// =============================================================================
// AUTONOMOUS TRADING SYSTEM TEST - BROWSER CONSOLE VERSION
// =============================================================================
// Copy and paste this entire script into browser console at:
// https://algoauto-9gx56.ondigitalocean.app

console.log("🚀 AUTONOMOUS TRADING SYSTEM DIAGNOSTIC");
console.log("🎯 Testing with REAL TrueData prices + Reauthorized Zerodha");
console.log("=" * 70);

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

async function testEndpoint(endpoint, method = 'GET', showData = true) {
    try {
        console.log(`\n🔍 Testing ${method} ${endpoint}...`);
        
        const options = { 
            method, 
            headers: { 'Content-Type': 'application/json' }
        };
        
        const response = await fetch(`${BASE_URL}${endpoint}`, options);
        const isJson = response.headers.get('content-type')?.includes('application/json');
        
        console.log(`   Status: ${response.status} ${response.ok ? '✅' : '❌'}`);
        
        if (response.ok && isJson && showData) {
            const data = await response.json();
            
            // Autonomous Status Details
            if (endpoint.includes('autonomous/status')) {
                const autonomousData = data.data || {};
                const isActive = autonomousData.is_active || false;
                const pnl = autonomousData.daily_pnl || 0;
                const positions = autonomousData.active_positions?.length || 0;
                const strategies = autonomousData.active_strategies?.length || 0;
                const sessionId = autonomousData.session_id || 'None';
                const startTime = autonomousData.start_time || 'Not started';
                
                console.log(`   🎯 Status: ${isActive ? '🟢 ACTIVE' : '🔴 INACTIVE'}`);
                console.log(`   💰 Daily P&L: ₹${pnl}`);
                console.log(`   📊 Active Positions: ${positions}`);
                console.log(`   🧠 Active Strategies: ${strategies}`);
                console.log(`   🆔 Session ID: ${sessionId}`);
                console.log(`   🕐 Start Time: ${startTime}`);
                
                return { isActive, pnl, positions, strategies, sessionId };
            }
            
            // TrueData Status Details  
            else if (endpoint.includes('truedata')) {
                const truedataData = data.data || {};
                const connected = truedataData.connected || false;
                const symbols = truedataData.total_symbols || 0;
                const subscribedSymbols = truedataData.subscribed_symbols || [];
                
                console.log(`   🌐 TrueData Connected: ${connected ? '✅ YES' : '❌ NO'}`);
                console.log(`   📈 Total Symbols: ${symbols}`);
                console.log(`   📊 Subscribed: ${subscribedSymbols.length}`);
                
                if (subscribedSymbols.length > 0) {
                    console.log(`   🔥 Sample Symbols: ${subscribedSymbols.slice(0, 3).join(', ')}`);
                }
                
                return { connected, symbols, subscribedCount: subscribedSymbols.length };
            }
            
            // Zerodha Auth Details
            else if (endpoint.includes('zerodha')) {
                const authenticated = data.authenticated || false;
                const profile = data.profile || {};
                const lastAuth = data.last_authenticated || 'Never';
                
                console.log(`   🔐 Zerodha Auth: ${authenticated ? '✅ AUTHENTICATED' : '❌ NOT AUTHENTICATED'}`);
                console.log(`   👤 User: ${profile.user_name || 'Unknown'}`);
                console.log(`   🕐 Last Auth: ${lastAuth}`);
                
                return { authenticated, profile, lastAuth };
            }
            
            // Generic Success Response
            else {
                const success = data.success !== false;
                const message = data.message || 'OK';
                console.log(`   ✅ Success: ${success}`);
                console.log(`   💬 Message: ${message}`);
                return { success, message, data };
            }
        } else if (!response.ok) {
            const errorText = await response.text();
            console.log(`   ❌ Error Response: ${errorText.substring(0, 200)}...`);
            return { error: true, status: response.status, message: errorText };
        }
        
        return { success: response.ok, status: response.status };
        
    } catch (error) {
        console.log(`   💥 Exception: ${error.message}`);
        return { error: true, exception: error.message };
    }
}

async function comprehensiveTest() {
    console.log("\n" + "=".repeat(70));
    console.log("🔬 COMPREHENSIVE SYSTEM TEST");
    console.log("=".repeat(70));
    
    // Test 1: System Health
    console.log("\n1️⃣ SYSTEM HEALTH CHECK");
    await testEndpoint('/health', 'GET', false);
    await testEndpoint('/ready', 'GET', false);
    
    // Test 2: Autonomous Trading Status
    console.log("\n2️⃣ AUTONOMOUS TRADING STATUS");
    const autonomousStatus = await testEndpoint('/api/v1/autonomous/status');
    const isCurrentlyActive = autonomousStatus?.isActive || false;
    
    // Test 3: Authentication Status
    console.log("\n3️⃣ AUTHENTICATION STATUS");
    const zerodhaAuth = await testEndpoint('/auth/zerodha/status');
    const isAuthenticated = zerodhaAuth?.authenticated || false;
    
    // Test 4: Market Data Status
    console.log("\n4️⃣ MARKET DATA STATUS");
    console.log("Testing multiple TrueData endpoints...");
    
    const truedataEndpoints = [
        '/api/v1/truedata/status',
        '/api/v1/truedata/truedata/status', 
        '/api/v1/market/indices'
    ];
    
    let truedataWorking = false;
    for (const endpoint of truedataEndpoints) {
        const result = await testEndpoint(endpoint);
        if (result?.connected || result?.success) {
            truedataWorking = true;
            break;
        }
    }
    
    // Test 5: Start Autonomous Trading (if not active)
    console.log("\n5️⃣ AUTONOMOUS TRADING CONTROL");
    if (!isCurrentlyActive) {
        console.log("🚀 Attempting to start autonomous trading...");
        const startResult = await testEndpoint('/api/v1/autonomous/start', 'POST');
        
        if (startResult?.success) {
            console.log("⏳ Waiting 3 seconds for initialization...");
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            console.log("📊 Checking status after start...");
            await testEndpoint('/api/v1/autonomous/status');
        }
    } else {
        console.log("✅ Autonomous trading is already ACTIVE!");
    }
    
    // Test 6: Additional Endpoints
    console.log("\n6️⃣ ADDITIONAL ENDPOINTS");
    await testEndpoint('/api/v1/autonomous/positions', 'GET', false);
    await testEndpoint('/api/v1/autonomous/performance', 'GET', false);
    
    // Summary
    console.log("\n" + "=".repeat(70));
    console.log("📋 SYSTEM SUMMARY");
    console.log("=".repeat(70));
    console.log(`🎯 Autonomous Trading: ${isCurrentlyActive ? '🟢 ACTIVE' : '🔴 INACTIVE'}`);
    console.log(`🔐 Zerodha Auth: ${isAuthenticated ? '✅ AUTHENTICATED' : '❌ NOT AUTHENTICATED'}`);
    console.log(`📊 Market Data: ${truedataWorking ? '✅ WORKING' : '❌ ISSUES DETECTED'}`);
    
    if (isAuthenticated && isCurrentlyActive) {
        console.log("\n🎉 SYSTEM STATUS: FULLY OPERATIONAL!");
        console.log("💰 Ready for live trading with real prices");
        console.log("🎯 Precision not speed - using REAL TrueData");
    } else {
        console.log("\n⚠️ SYSTEM STATUS: NEEDS ATTENTION");
        if (!isAuthenticated) console.log("   - Zerodha reauthorization required");
        if (!isCurrentlyActive) console.log("   - Autonomous trading needs to be started");
        if (!truedataWorking) console.log("   - Market data connection issues");
    }
    
    console.log("\n🔄 Test completed. Run comprehensiveTest() again to refresh.");
}

// Auto-run the comprehensive test
comprehensiveTest(); 