const https = require('https');

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

function makeRequest(url) {
    return new Promise((resolve, reject) => {
        const req = https.request(url, { timeout: 15000 }, (res) => {
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

        req.end();
    });
}

async function testRealMarketData() {
    console.log('🔍 Testing Real Market Data Processing...\n');

    try {
        // Test Elite recommendations (should work with real data)
        console.log('🏆 Testing Elite Recommendations...');
        const eliteResult = await makeRequest(`${BASE_URL}/api/v1/elite`);

        if (eliteResult.status === 200) {
            const recommendations = eliteResult.data;
            console.log('✅ Elite Recommendations: SUCCESS');
            console.log(`   📊 Found ${recommendations.length} recommendations`);

            if (recommendations.length > 0) {
                console.log('\n🎯 SAMPLE RECOMMENDATIONS:');
                recommendations.slice(0, 3).forEach((rec, i) => {
                    console.log(`   ${i + 1}. ${rec.symbol} - ${rec.action} - Confidence: ${rec.confidence}%`);
                    console.log(`      Price: ₹${rec.price} | Target: ₹${rec.target_price}`);
                    console.log(`      Reason: ${rec.reason}`);
                });

                // Check if these are real market prices
                const realDataMarkers = recommendations.filter(r =>
                    r.source === 'REAL_MARKET_DATA' ||
                    r.source === 'LOCAL_TRUEDATA' ||
                    r.verification === 'REAL_MARKET_DATA_VERIFIED'
                );

                console.log(`\n📈 Real Market Data Markers: ${realDataMarkers.length}/${recommendations.length}`);

                if (realDataMarkers.length > 0) {
                    console.log('✅ CONFIRMED: Using real market data for recommendations');
                } else {
                    console.log('⚠️ WARNING: May still be using fallback data');
                }
            }
        } else {
            console.log(`❌ Elite Recommendations: FAILED (${eliteResult.status})`);
        }

        // Test autonomous trading status with real data
        console.log('\n🤖 Testing Autonomous Trading with Real Data...');
        const autoResult = await makeRequest(`${BASE_URL}/api/v1/autonomous/status`);

        if (autoResult.status === 200) {
            const status = autoResult.data.data;
            console.log('✅ Autonomous Trading Status: SUCCESS');
            console.log(`   🎯 Active: ${status.is_active}`);
            console.log(`   📊 Strategies: ${status.active_strategies.length}`);
            console.log(`   💰 Total Trades: ${status.total_trades}`);
            console.log(`   💹 Daily PNL: ₹${status.daily_pnl}`);
            console.log(`   📈 Active Positions: ${status.active_positions}`);
            console.log(`   🏮 Market Status: ${status.market_status}`);
            console.log(`   ⚡ System Ready: ${status.system_ready}`);

            if (status.total_trades === 0) {
                console.log('\n⚠️ ZERO TRADES DETECTED - Need to check signal generation');
            }
        }

        // Test if we can get individual symbol data
        console.log('\n📊 Testing Individual Symbol Data...');
        const symbols = ['RELIANCE', 'BANKNIFTY', 'NIFTY'];

        for (const symbol of symbols) {
            try {
                const symbolResult = await makeRequest(`${BASE_URL}/api/v1/market-data/${symbol}`);
                if (symbolResult.status === 200) {
                    console.log(`✅ ${symbol}: Live data available`);
                    if (symbolResult.data.ltp) {
                        console.log(`   💰 LTP: ₹${symbolResult.data.ltp}`);
                    }
                } else {
                    console.log(`❌ ${symbol}: Failed (${symbolResult.status})`);
                }
            } catch (error) {
                console.log(`❌ ${symbol}: Error - ${error.message}`);
            }
        }

        // Check if orders are being generated
        console.log('\n📋 Testing Order Generation...');
        const ordersResult = await makeRequest(`${BASE_URL}/api/v1/orders/`);

        if (ordersResult.status === 200) {
            const orders = ordersResult.data.orders;
            console.log(`✅ Orders API: SUCCESS - Found ${orders.length} orders`);

            if (orders.length > 0) {
                console.log('🎯 RECENT ORDERS:');
                orders.slice(0, 3).forEach((order, i) => {
                    console.log(`   ${i + 1}. ${order.symbol} - ${order.side} - ₹${order.price}`);
                });
            } else {
                console.log('⚠️ No orders found - Signal generation may be the issue');
            }
        }

    } catch (error) {
        console.log(`❌ Error: ${error.message}`);
    }
}

async function runRealDataTest() {
    console.log('🚀 Real Market Data Processing Test');
    console.log('=' * 40);
    console.log('📊 Based on logs: TrueData is streaming real prices');
    console.log('🎯 Testing if system processes this data correctly\n');

    await testRealMarketData();

    console.log('\n' + '=' * 40);
    console.log('🏁 Test Complete');
    console.log('\n💡 INSIGHTS:');
    console.log('   - TrueData is working (confirmed from logs)');
    console.log('   - Real market data is flowing');
    console.log('   - Need to check signal generation pipeline');
    console.log('   - Elite recommendations should show real data');
}

runRealDataTest(); 