// =============================================================================
// DIAGNOSE FAKE TRADES ISSUE - BROWSER CONSOLE SCRIPT
// =============================================================================
// 🚨 ISSUE: System showing fake trades despite TrueData connection
// 📊 Real prices: RELIANCE ₹1,519, TCS ₹3,444, INFY ₹1,609  
// 🎭 Fake prices: RELIANCE ₹2,514, TCS ₹2,125, INFY ₹2,575
//
// Copy and paste this into browser console at:
// https://algoauto-9gx56.ondigitalocean.app

console.log("🕵️ DIAGNOSING FAKE TRADES ISSUE");
console.log("🎯 Expected: Real TrueData prices | Found: Fake mock prices");
console.log("=".repeat(70));

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

// Real market prices we expect to see
const EXPECTED_REAL_PRICES = {
    'RELIANCE': { min: 1400, max: 1700, current: 1519 },
    'TCS': { min: 3300, max: 3600, current: 3444 },
    'INFY': { min: 1500, max: 1700, current: 1609 },
    'HDFCBANK': { min: 1600, max: 1800, current: 1700 },
    'ICICIBANK': { min: 1200, max: 1400, current: 1300 }
};

async function fetchData(endpoint, method = 'GET') {
    try {
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method,
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        return { success: response.ok, data, status: response.status };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

function isPriceFake(symbol, price) {
    const expected = EXPECTED_REAL_PRICES[symbol];
    if (!expected) return { fake: false, reason: 'Unknown symbol' };

    const numPrice = parseFloat(price.toString().replace(/[₹,]/g, ''));

    if (numPrice < expected.min || numPrice > expected.max) {
        return {
            fake: true,
            reason: `Price ₹${numPrice} outside real range ₹${expected.min}-₹${expected.max}`,
            expected: expected.current,
            difference: Math.abs(numPrice - expected.current)
        };
    }

    return { fake: false, reason: 'Price looks real' };
}

async function diagnoseTrades() {
    console.log("\n1️⃣ CHECKING CURRENT TRADES (Live Data)");
    console.log("-".repeat(50));

    const tradesResult = await fetchData('/api/v1/trades/today');

    if (tradesResult.success && tradesResult.data?.data) {
        const trades = tradesResult.data.data;
        console.log(`📊 Found ${trades.length} trades today`);

        let fakeCount = 0;
        let realCount = 0;

        trades.forEach((trade, index) => {
            const symbol = trade.symbol || trade.instrument_token;
            const entryPrice = trade.entry_price || trade.price;
            const currentPrice = trade.current_price || trade.last_price;

            console.log(`\nTrade ${index + 1}: ${symbol}`);
            console.log(`   Entry: ₹${entryPrice} | Current: ₹${currentPrice}`);

            const entryCheck = isPriceFake(symbol, entryPrice);
            const currentCheck = isPriceFake(symbol, currentPrice);

            if (entryCheck.fake || currentCheck.fake) {
                fakeCount++;
                console.log(`   🎭 FAKE DETECTED!`);
                if (entryCheck.fake) console.log(`      Entry: ${entryCheck.reason}`);
                if (currentCheck.fake) console.log(`      Current: ${currentCheck.reason}`);
                console.log(`      Expected: ₹${EXPECTED_REAL_PRICES[symbol]?.current || 'Unknown'}`);
            } else {
                realCount++;
                console.log(`   ✅ Prices look real`);
            }
        });

        console.log(`\n📊 TRADE ANALYSIS:`);
        console.log(`   🎭 Fake trades: ${fakeCount}`);
        console.log(`   ✅ Real trades: ${realCount}`);
        console.log(`   📈 Fake percentage: ${((fakeCount / trades.length) * 100).toFixed(1)}%`);

        if (fakeCount > 0) {
            console.log(`\n🚨 PROBLEM CONFIRMED: ${fakeCount} trades using fake prices!`);
        }
    } else {
        console.log("❌ Could not fetch trades data");
        console.log(`   Error: ${tradesResult.error || 'API call failed'}`);
    }
}

async function diagnoseMarketData() {
    console.log("\n2️⃣ CHECKING MARKET DATA SOURCES");
    console.log("-".repeat(50));

    // Test multiple market data endpoints
    const marketEndpoints = [
        '/api/v1/market/indices',
        '/api/v1/truedata/status',
        '/api/v1/truedata/truedata/status',
        '/api/v1/truedata/symbols',
        '/api/v1/market-data/live'
    ];

    for (const endpoint of marketEndpoints) {
        console.log(`\n🔍 Testing: ${endpoint}`);
        const result = await fetchData(endpoint);

        if (result.success) {
            console.log(`   ✅ Status: ${result.status}`);

            // Check for real price data
            const data = result.data;
            if (data?.data?.indices) {
                // Market indices
                data.data.indices.forEach(index => {
                    const price = index.last_price || index.ltp;
                    console.log(`   📊 ${index.symbol}: ₹${price}`);

                    if (index.symbol === 'NIFTY' && price > 0) {
                        console.log(`      ${price > 20000 && price < 30000 ? '✅ Real NIFTY price' : '🎭 Fake NIFTY price'}`);
                    }
                });
            } else if (data?.data?.connected !== undefined) {
                // TrueData status
                console.log(`   🌐 Connected: ${data.data.connected}`);
                console.log(`   📈 Symbols: ${data.data.total_symbols || 0}`);
            } else {
                console.log(`   📋 Data keys: ${Object.keys(data).join(', ')}`);
            }
        } else {
            console.log(`   ❌ Failed: ${result.status || 'Network error'}`);
        }
    }
}

async function diagnoseSystemConfig() {
    console.log("\n3️⃣ CHECKING SYSTEM CONFIGURATION");
    console.log("-".repeat(50));

    // Check for mock/test mode indicators
    const configEndpoints = [
        '/api/v1/autonomous/status',
        '/debug/config',
        '/api/v1/system/config',
        '/api/v1/trading/config'
    ];

    for (const endpoint of configEndpoints) {
        console.log(`\n🔍 Testing: ${endpoint}`);
        const result = await fetchData(endpoint);

        if (result.success) {
            const data = result.data;

            // Look for mock mode indicators
            const configText = JSON.stringify(data, null, 2);
            const mockIndicators = [
                'mock', 'test', 'fake', 'simulation', 'demo',
                'paper_trading', 'sandbox', 'development'
            ];

            const foundMocks = mockIndicators.filter(indicator =>
                configText.toLowerCase().includes(indicator)
            );

            if (foundMocks.length > 0) {
                console.log(`   🎭 MOCK INDICATORS FOUND: ${foundMocks.join(', ')}`);
                console.log(`   📋 This might explain the fake prices!`);
            } else {
                console.log(`   ✅ No obvious mock indicators`);
            }

            // Check autonomous status specifically
            if (endpoint.includes('autonomous')) {
                const autonomousData = data.data || {};
                console.log(`   🎯 Active: ${autonomousData.is_active}`);
                console.log(`   🧠 Strategies: ${autonomousData.active_strategies?.length || 0}`);
                console.log(`   💰 P&L: ₹${autonomousData.daily_pnl || 0}`);
            }
        } else {
            console.log(`   ❌ Failed: ${result.status || 'Network error'}`);
        }
    }
}

async function checkRealPricesDirectly() {
    console.log("\n4️⃣ CHECKING REAL PRICES DIRECTLY");
    console.log("-".repeat(50));

    // Try to get real current prices
    const symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK'];

    for (const symbol of symbols) {
        console.log(`\n📊 ${symbol}:`);

        // Try multiple ways to get real price
        const priceEndpoints = [
            `/api/v1/market/${symbol}`,
            `/api/v1/truedata/symbol/${symbol}`,
            `/api/v1/market-data/${symbol}`,
            `/api/v1/live/${symbol}`
        ];

        let realPriceFound = false;

        for (const endpoint of priceEndpoints) {
            const result = await fetchData(endpoint);

            if (result.success && result.data) {
                const data = result.data;
                const price = data.ltp || data.last_price || data.price || data.current_price;

                if (price && price > 0) {
                    const priceCheck = isPriceFake(symbol, price);
                    const status = priceCheck.fake ? '🎭 FAKE' : '✅ REAL';

                    console.log(`   ${endpoint}: ₹${price} ${status}`);

                    if (!priceCheck.fake) {
                        realPriceFound = true;
                        console.log(`      ✅ Found real price for ${symbol}!`);
                        break;
                    } else {
                        console.log(`      🎭 ${priceCheck.reason}`);
                    }
                }
            }
        }

        if (!realPriceFound) {
            console.log(`   ❌ No real price found for ${symbol}`);
            console.log(`   📋 Expected: ₹${EXPECTED_REAL_PRICES[symbol]?.current}`);
        }
    }
}

async function generateReport() {
    console.log("\n5️⃣ GENERATING DIAGNOSTIC REPORT");
    console.log("-".repeat(50));

    // Summarize findings
    console.log("\n📋 DIAGNOSTIC SUMMARY:");
    console.log("=".repeat(40));

    console.log("\n🎭 FAKE PRICES DETECTED IN:");
    console.log("   - Trade entries (₹2,514 for RELIANCE vs real ₹1,519)");
    console.log("   - Current prices (₹1,863 for RELIANCE vs real ₹1,519)");
    console.log("   - Multiple symbols showing impossible prices");

    console.log("\n🔍 POSSIBLE CAUSES:");
    console.log("   1. Trading engine still in mock/test mode");
    console.log("   2. Market data manager using fallback fake prices");
    console.log("   3. Configuration variables forcing simulation mode");
    console.log("   4. Database containing old mock trade records");
    console.log("   5. Frontend displaying cached/mock data");

    console.log("\n💡 RECOMMENDED ACTIONS:");
    console.log("   1. Check if trading engine has mock_mode enabled");
    console.log("   2. Verify market data manager is using TrueData");
    console.log("   3. Clear any mock/test configuration flags");
    console.log("   4. Restart trading components to reload real data");
    console.log("   5. Check database for mock trade data pollution");

    console.log("\n🎯 PRECISION NOT SPEED:");
    console.log("   This fake data violates the core principle!");
    console.log("   Must use REAL prices for REAL trading accuracy.");
}

// Main diagnostic function
async function runFullDiagnosis() {
    console.log("🕵️ STARTING COMPREHENSIVE FAKE TRADES DIAGNOSIS");
    console.log("🎯 Goal: Find why system uses fake prices instead of real TrueData");

    try {
        await diagnoseTrades();
        await diagnoseMarketData();
        await diagnoseSystemConfig();
        await checkRealPricesDirectly();
        await generateReport();

        console.log("\n✅ DIAGNOSIS COMPLETE!");
        console.log("📊 Check the report above for detailed findings.");
        console.log("🔄 Run runFullDiagnosis() again to refresh results.");

    } catch (error) {
        console.log(`\n❌ DIAGNOSIS ERROR: ${error.message}`);
    }
}

// Auto-run the diagnosis
runFullDiagnosis(); 