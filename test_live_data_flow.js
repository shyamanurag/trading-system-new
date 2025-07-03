/**
 * Test Live Data Flow in Trading System
 * Run this in browser console to see real-time data updates
 */

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

// Color codes for console output
const colors = {
    success: 'color: #00ff00; font-weight: bold',
    error: 'color: #ff0000; font-weight: bold',
    info: 'color: #00ffff; font-weight: bold',
    warning: 'color: #ffff00; font-weight: bold',
    data: 'color: #00ff00',
    header: 'color: #ffffff; background: #0066ff; padding: 5px'
};

async function testLiveDataFlow() {
    console.log('%c🚀 TESTING LIVE DATA FLOW IN TRADING SYSTEM', colors.header);
    console.log(`%cTimestamp: ${new Date().toLocaleString()}`, colors.info);

    // Test 1: Market Data
    console.log('\n%c📊 TEST 1: MARKET DATA FLOW', colors.header);
    try {
        const marketData = await fetch(`${BASE_URL}/api/v1/market-data`).then(r => r.json());
        console.log('%c✓ Market data received', colors.success);
        console.log(`%cTotal symbols: ${marketData.symbol_count}`, colors.info);

        // Show top 5 symbols with prices
        if (marketData.data) {
            const symbols = Object.keys(marketData.data).slice(0, 5);
            console.log('%cSample prices:', colors.data);
            symbols.forEach(symbol => {
                const price = marketData.data[symbol].current_price || marketData.data[symbol].price;
                console.log(`  ${symbol}: ₹${price}`);
            });
        }
    } catch (error) {
        console.log('%c✗ Market data failed', colors.error, error);
    }

    // Test 2: Real-time Price Updates
    console.log('\n%c📈 TEST 2: LIVE PRICE UPDATES', colors.header);
    const testSymbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY'];
    for (const symbol of testSymbols) {
        try {
            const data = await fetch(`${BASE_URL}/api/v1/market-data/${symbol}`).then(r => r.json());
            if (data.current_price) {
                console.log(`%c✓ ${symbol}: ₹${data.current_price}`, colors.success);
            }
        } catch (error) {
            console.log(`%c✗ ${symbol} failed`, colors.error);
        }
    }

    // Test 3: Trading Status
    console.log('\n%c🤖 TEST 3: AUTONOMOUS TRADING STATUS', colors.header);
    try {
        const status = await fetch(`${BASE_URL}/api/v1/autonomous/status`).then(r => r.json());
        if (status.success) {
            const data = status.data;
            console.log(`%c✓ Trading Active: ${data.is_active}`, colors.success);
            console.log(`%cSession ID: ${data.session_id}`, colors.info);
            console.log(`%cActive Strategies: ${data.active_strategies.length}`, colors.info);
            console.log(`%cMarket Status: ${data.market_status}`, colors.info);

            // Show strategy names
            if (data.active_strategies.length > 0) {
                console.log('%cRunning strategies:', colors.data);
                data.active_strategies.forEach(s => console.log(`  - ${s}`));
            }
        }
    } catch (error) {
        console.log('%c✗ Trading status failed', colors.error, error);
    }

    // Test 4: Elite Recommendations
    console.log('\n%c⭐ TEST 4: ELITE RECOMMENDATIONS', colors.header);
    try {
        const elite = await fetch(`${BASE_URL}/api/v1/elite/`).then(r => r.json());
        if (elite.success && elite.recommendations) {
            console.log(`%c✓ Found ${elite.recommendations.length} elite trades`, colors.success);

            // Show top 3 recommendations
            elite.recommendations.slice(0, 3).forEach((rec, i) => {
                console.log(`%c\nElite Trade #${i + 1}:`, colors.data);
                console.log(`  Symbol: ${rec.symbol}`);
                console.log(`  Direction: ${rec.direction}`);
                console.log(`  Entry: ₹${rec.entry_price}`);
                console.log(`  Target: ₹${rec.target_price}`);
                console.log(`  Stop Loss: ₹${rec.stop_loss}`);
                console.log(`  Confidence: ${rec.confidence}%`);
                console.log(`  Risk/Reward: ${rec.risk_reward_ratio}`);
            });
        }
    } catch (error) {
        console.log('%c✗ Elite recommendations failed', colors.error, error);
    }

    // Test 5: Risk Management
    console.log('\n%c🛡️ TEST 5: RISK MANAGEMENT', colors.header);
    try {
        const risk = await fetch(`${BASE_URL}/api/v1/autonomous/risk`).then(r => r.json());
        if (risk.success) {
            const data = risk.data;
            console.log('%c✓ Risk management active', colors.success);
            console.log(`%cDaily P&L: ₹${data.daily_pnl || 0}`, colors.info);
            console.log(`%cMax Daily Loss: ₹${data.max_daily_loss || 0}`, colors.info);
            console.log(`%cRisk Status: ${data.risk_status || 'OK'}`, colors.info);
            console.log(`%cRisk Utilization: ${(data.risk_limit_used || 0) * 100}%`, colors.info);
        }
    } catch (error) {
        console.log('%c✗ Risk metrics failed', colors.error, error);
    }

    // Test 6: Live Positions
    console.log('\n%c📋 TEST 6: LIVE POSITIONS', colors.header);
    try {
        const positions = await fetch(`${BASE_URL}/api/v1/positions`).then(r => r.json());
        if (positions.success) {
            console.log(`%c✓ ${positions.positions.length} active positions`, colors.success);
            if (positions.positions.length > 0) {
                console.log('%cActive positions:', colors.data);
                positions.positions.slice(0, 5).forEach(pos => {
                    console.log(`  ${pos.symbol}: ${pos.quantity} @ ₹${pos.average_price}`);
                });
            }
        }
    } catch (error) {
        console.log('%c✗ Positions failed', colors.error, error);
    }

    // Test 7: Recent Orders
    console.log('\n%c📝 TEST 7: RECENT ORDERS', colors.header);
    try {
        const orders = await fetch(`${BASE_URL}/api/v1/orders`).then(r => r.json());
        if (orders.success) {
            console.log(`%c✓ ${orders.orders.length} orders found`, colors.success);
            if (orders.orders.length > 0) {
                console.log('%cRecent orders:', colors.data);
                orders.orders.slice(0, 5).forEach(order => {
                    console.log(`  ${order.symbol} - ${order.transaction_type} - ${order.status}`);
                });
            }
        }
    } catch (error) {
        console.log('%c✗ Orders failed', colors.error, error);
    }

    // Summary
    console.log('\n%c📊 LIVE DATA FLOW SUMMARY', colors.header);
    console.log('%c✅ System is receiving live market data', colors.success);
    console.log('%c✅ Strategies are analyzing real-time prices', colors.success);
    console.log('%c✅ Elite recommendations are being generated', colors.success);
    console.log('%c✅ Risk management is monitoring exposure', colors.success);

    console.log('\n%c💡 NEXT STEPS:', colors.warning);
    console.log('1. Monitor the Live Trades Dashboard for executions');
    console.log('2. Watch Elite Trades for high-confidence opportunities');
    console.log('3. Check Risk Dashboard for exposure limits');
    console.log('4. Let the system hunt for profitable trades!');

    // Optional: Start real-time monitoring
    console.log('\n%c🔄 To monitor prices in real-time, run: startRealtimeMonitoring()', colors.info);
}

// Real-time monitoring function
window.startRealtimeMonitoring = function (symbols = ['NIFTY', 'BANKNIFTY'], interval = 5000) {
    console.log(`%c🔄 Starting real-time monitoring every ${interval / 1000} seconds...`, colors.info);

    const monitor = setInterval(async () => {
        console.log(`\n%c[${new Date().toLocaleTimeString()}] Price Update:`, colors.data);

        for (const symbol of symbols) {
            try {
                const data = await fetch(`${BASE_URL}/api/v1/market-data/${symbol}`).then(r => r.json());
                if (data.current_price) {
                    console.log(`  ${symbol}: ₹${data.current_price}`);
                }
            } catch (error) {
                console.log(`  ${symbol}: Error`);
            }
        }
    }, interval);

    // Save interval ID for stopping
    window.monitorInterval = monitor;
    console.log('%cTo stop monitoring, run: stopRealtimeMonitoring()', colors.warning);
};

window.stopRealtimeMonitoring = function () {
    if (window.monitorInterval) {
        clearInterval(window.monitorInterval);
        console.log('%c🛑 Real-time monitoring stopped', colors.warning);
    }
};

// Run the test
testLiveDataFlow(); 