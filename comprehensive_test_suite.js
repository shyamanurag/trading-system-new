/**
 * COMPREHENSIVE SYSTEM TEST SUITE
 * ===============================
 * Tests all deployed fixes and system functionality
 * 
 * COPY THIS ENTIRE CODE AND PASTE IN BROWSER CONSOLE
 */

async function runComprehensiveTestSuite() {
    console.log('🚀 COMPREHENSIVE SYSTEM TEST SUITE + STRATEGY EXECUTION TESTS');
    console.log('==============================================================');
    console.log('Testing all deployed fixes AND strategy execution...\n');

    const baseUrl = 'https://algoauto-9gx56.ondigitalocean.app';
    let passedTests = 0;
    let totalTests = 0;

    // Helper function for tests
    function testResult(testName, passed, details = '') {
        totalTests++;
        if (passed) {
            passedTests++;
            console.log(`✅ ${testName}: PASS ${details}`);
        } else {
            console.log(`❌ ${testName}: FAIL ${details}`);
        }
    }

    try {
        // Test 1: CRITICAL - Orchestrator Status Endpoint (MAIN FIX)
        console.log('🔧 TEST 1: Orchestrator Status Endpoint (CRITICAL FIX)');
        console.log('======================================================');

        const orchResponse = await fetch(`${baseUrl}/api/v1/monitoring/orchestrator-status`);
        testResult('Orchestrator Endpoint Available', orchResponse.status === 200, `(Status: ${orchResponse.status})`);

        if (orchResponse.ok) {
            const orchData = await orchResponse.json();
            testResult('Orchestrator Response Valid', orchData.success === true);

            // CRITICAL TEST: Trade Engine Component
            const tradeEngineActive = orchData.components?.trade_engine === true;
            testResult('Trade Engine Component ACTIVE', tradeEngineActive, tradeEngineActive ? '(FIXED!)' : '(Still inactive)');

            testResult('System Components Present', Object.keys(orchData.components || {}).length >= 4);

            console.log('\n📊 Orchestrator Details:');
            console.log('- Running:', orchData.running);
            console.log('- Trade Engine Component:', orchData.components?.trade_engine ? '✅ ACTIVE' : '❌ INACTIVE');
            console.log('- Zerodha Component:', orchData.components?.zerodha_client ? '✅ ACTIVE' : '❌ INACTIVE');
            console.log('- Components Ready:', orchData.components_ready + '/' + orchData.total_components);
            console.log('- System Ready:', orchData.system_ready);
            console.log('- Trading Active:', orchData.trading_active);
            console.log('- All Components:', Object.keys(orchData.components || {}));
        }

        // Test 2: Elite Recommendations Strategy-Based Fix
        console.log('\n\n🎯 TEST 2: Elite Recommendations (Strategy-Based Fix)');
        console.log('====================================================');

        const eliteResponse = await fetch(`${baseUrl}/api/v1/elite/force-scan`, { method: 'POST' });
        testResult('Elite Force Scan Available', eliteResponse.status === 200);

        if (eliteResponse.ok) {
            const eliteData = await eliteResponse.json();
            testResult('Elite Scan Success', eliteData.success === true);

            // CRITICAL TEST: Strategy-Based vs Hardcoded
            const strategiesUsed = eliteData.strategies_used && eliteData.strategies_used.length > 0;
            testResult('Using Real Trading Strategies', strategiesUsed, strategiesUsed ? '(FIXED!)' : '(Still hardcoded)');

            testResult('Recommendations Generated', eliteData.recommendations_found > 0, `(${eliteData.recommendations_found} found)`);

            console.log('\n📊 Elite Recommendations Details:');
            console.log('- Strategies Used:', eliteData.strategies_used || 'None');
            console.log('- Recommendations Found:', eliteData.recommendations_found);

            if (eliteData.recommendations && eliteData.recommendations.length > 0) {
                const sample = eliteData.recommendations[0];
                console.log('- Sample Strategy:', sample.strategy);
                console.log('- Data Source:', sample.data_source);
                console.log('- Symbol:', sample.symbol);
                console.log('- Confidence:', sample.confidence + '%');

                const isStrategyBased = sample.data_source === 'STRATEGY_GENERATED';
                testResult('Strategy-Generated Data Source', isStrategyBased, isStrategyBased ? '(FIXED!)' : '(Still using old logic)');
            }
        }

        // Test 3: System Health
        console.log('\n\n🏥 TEST 3: System Health');
        console.log('========================');

        const healthResponse = await fetch(`${baseUrl}/api/v1/monitoring/health`);
        testResult('Health Endpoint Available', healthResponse.status === 200);

        if (healthResponse.ok) {
            const healthData = await healthResponse.json();
            testResult('Health Response Valid', healthData.success === true);
            console.log('\n📊 Health Details:');
            console.log('- Components:', Object.keys(healthData.components || {}));
            console.log('- Memory Usage:', healthData.memory_usage + '%');
            console.log('- CPU Usage:', healthData.cpu_usage + '%');
        }

        // Test 4: Trading System Status
        console.log('\n\n⚙️ TEST 4: Trading System Status');
        console.log('================================');

        const tradingResponse = await fetch(`${baseUrl}/api/v1/autonomous/status`);
        testResult('Trading Status Available', tradingResponse.status === 200);

        if (tradingResponse.ok) {
            const tradingData = await tradingResponse.json();
            testResult('Trading Status Valid', tradingData.success === true);
            console.log('\n📊 Trading Details:');
            console.log('- Is Active:', tradingData.is_active);
            console.log('- Active Strategies:', tradingData.active_strategies);
            console.log('- System Ready:', tradingData.system_ready);
            console.log('- Session ID:', tradingData.session_id);
        }

        // Test 5: Orders API
        console.log('\n\n📋 TEST 5: Orders API');
        console.log('=====================');

        const ordersResponse = await fetch(`${baseUrl}/api/v1/orders/`);
        testResult('Orders Endpoint Available', ordersResponse.status === 200);

        if (ordersResponse.ok) {
            const ordersData = await ordersResponse.json();
            testResult('Orders Response Valid', ordersData.orders !== undefined);
            console.log('\n📊 Orders Details:');
            console.log('- Total Orders:', ordersData.orders?.length || 0);
            console.log('- API Success:', ordersData.success !== false);
        }

        // Test 6: Market Data
        console.log('\n\n📈 TEST 6: Market Data');
        console.log('======================');

        const marketResponse = await fetch(`${baseUrl}/api/v1/market-data`);
        testResult('Market Data Available', marketResponse.status === 200);

        if (marketResponse.ok) {
            const marketData = await marketResponse.json();
            testResult('Market Data Valid', marketData.success === true);
            testResult('Symbols Available', marketData.symbol_count > 0, `(${marketData.symbol_count} symbols)`);
            console.log('\n📊 Market Data Details:');
            console.log('- Symbol Count:', marketData.symbol_count);
            console.log('- Data Source:', marketData.source);
        }

        // Test 7: Complete Elite Recommendations Test
        console.log('\n\n🔍 TEST 7: Elite Recommendations Complete Test');
        console.log('==============================================');

        const eliteGetResponse = await fetch(`${baseUrl}/api/v1/elite`);
        testResult('Elite GET Endpoint Available', eliteGetResponse.status === 200);

        if (eliteGetResponse.ok) {
            const eliteGetData = await eliteGetResponse.json();
            testResult('Elite GET Response Valid', eliteGetData.success === true);
            console.log('\n📊 Elite GET Details:');
            console.log('- Total Count:', eliteGetData.total_count);
            console.log('- Data Source:', eliteGetData.data_source);
            console.log('- Strategies Used:', eliteGetData.strategies_used);
            console.log('- Cache Status:', eliteGetData.cache_status);
        }

        // Test 8: 🔥 NEW - STRATEGY EXECUTION TESTS
        console.log('\n\n🔥 TEST 8: STRATEGY EXECUTION TESTS (CRITICAL FOR TRADES)');
        console.log('=========================================================');

        // Test 8a: Trading System Status
        const tradingStatusResponse = await fetch(`${baseUrl}/api/v1/autonomous/status`);
        testResult('Trading System Status Available', tradingStatusResponse.status === 200);

        if (tradingStatusResponse.ok) {
            const tradingStatus = await tradingStatusResponse.json();
            testResult('Trading System Response Valid', tradingStatus.success === true);

            const isActive = tradingStatus.is_active === true;
            testResult('Trading System ACTIVE', isActive, isActive ? '(TRADING ON!)' : '(TRADING OFF!)');

            console.log('\n📊 Trading System Details:');
            console.log('- Is Active:', tradingStatus.is_active);
            console.log('- Active Strategies:', tradingStatus.active_strategies);
            console.log('- System Ready:', tradingStatus.system_ready);
            console.log('- Session ID:', tradingStatus.session_id);

            // If trading is not active, this is why no trades!
            if (!isActive) {
                console.log('🚨 CRITICAL: Trading system is NOT ACTIVE - This is why no trades!');
            }
        }

        // Test 8b: Strategy Management API
        const strategyResponse = await fetch(`${baseUrl}/api/v1/strategies/status`);
        testResult('Strategy Management Available', strategyResponse.status === 200);

        if (strategyResponse.ok) {
            const strategyData = await strategyResponse.json();
            testResult('Strategy Management Valid', strategyData.success === true);

            const activeStrategies = strategyData.active_strategies || [];
            testResult('Active Strategies Present', activeStrategies.length > 0, `(${activeStrategies.length} strategies)`);

            console.log('\n📊 Strategy Management Details:');
            console.log('- Active Strategies:', activeStrategies);
            console.log('- Total Strategies:', strategyData.total_strategies);
            console.log('- Strategy Status:', strategyData.strategy_status);

            if (activeStrategies.length === 0) {
                console.log('🚨 CRITICAL: No active strategies - This is why no trades!');
            }
        }

        // Test 8c: Check if Autonomous Trading is Started
        const autonomousStartResponse = await fetch(`${baseUrl}/api/v1/autonomous/start`, { method: 'POST' });
        testResult('Autonomous Trading Start Available', autonomousStartResponse.status === 200);

        if (autonomousStartResponse.ok) {
            const autonomousData = await autonomousStartResponse.json();
            testResult('Autonomous Trading Start Valid', autonomousData.success === true);

            console.log('\n📊 Autonomous Trading Start Details:');
            console.log('- Success:', autonomousData.success);
            console.log('- Message:', autonomousData.message);
            console.log('- Active Strategies:', autonomousData.active_strategies);

            if (autonomousData.success && autonomousData.active_strategies > 0) {
                console.log('✅ GOOD: Autonomous trading started with strategies!');
            } else {
                console.log('🚨 ISSUE: Autonomous trading may not be properly started!');
            }
        }

        // Test 9: Orders API (Check for Recent Trades)
        console.log('\n\n📋 TEST 9: ORDERS & TRADES (ZERO TRADES INVESTIGATION)');
        console.log('======================================================');

        const ordersResponseCheck = await fetch(`${baseUrl}/api/v1/orders/`);
        testResult('Orders Endpoint Available', ordersResponseCheck.status === 200);

        if (ordersResponseCheck.ok) {
            const ordersDataCheck = await ordersResponseCheck.json();
            testResult('Orders Response Valid', ordersDataCheck.orders !== undefined);

            const totalOrdersCheck = ordersDataCheck.orders?.length || 0;
            testResult('Orders Present', totalOrdersCheck > 0, `(${totalOrdersCheck} orders)`);

            console.log('\n📊 Orders Investigation:');
            console.log('- Total Orders:', totalOrdersCheck);
            console.log('- Recent Orders:', ordersDataCheck.orders?.slice(0, 5) || 'None');

            if (totalOrdersCheck === 0) {
                console.log('🚨 CONFIRMED: ZERO TRADES - Need to investigate why strategies aren\'t executing!');
            }
        }

        // Test 10: Market Data (Required for Strategy Execution)
        console.log('\n\n📈 TEST 10: MARKET DATA (STRATEGY FUEL)');
        console.log('======================================');

        const marketResponseCheck = await fetch(`${baseUrl}/api/v1/market-data`);
        testResult('Market Data Available', marketResponseCheck.status === 200);

        if (marketResponseCheck.ok) {
            const marketDataCheck = await marketResponseCheck.json();
            testResult('Market Data Valid', marketDataCheck.success === true);
            testResult('Symbols Available', marketDataCheck.symbol_count > 0, `(${marketDataCheck.symbol_count} symbols)`);

            console.log('\n📊 Market Data Details:');
            console.log('- Symbol Count:', marketDataCheck.symbol_count);
            console.log('- Data Source:', marketDataCheck.source);
            console.log('- Last Updated:', marketDataCheck.last_updated);

            if (marketDataCheck.symbol_count === 0) {
                console.log('🚨 CRITICAL: No market data - Strategies can\'t work without data!');
            }
        }

        // Test 11: 🔥 NEW - SIGNAL GENERATION TEST
        console.log('\n\n🔥 TEST 11: SIGNAL GENERATION TEST');
        console.log('==================================');

        // Check if signals are being generated
        const signalResponse = await fetch(`${baseUrl}/api/v1/signals/recent`);
        if (signalResponse.status === 200) {
            const signalData = await signalResponse.json();
            testResult('Signal Generation Available', signalData.success === true);

            const recentSignals = signalData.signals?.length || 0;
            testResult('Recent Signals Generated', recentSignals > 0, `(${recentSignals} signals)`);

            console.log('\n📊 Signal Generation:');
            console.log('- Recent Signals:', recentSignals);
            console.log('- Signal Details:', signalData.signals?.slice(0, 3) || 'None');

            if (recentSignals === 0) {
                console.log('🚨 CRITICAL: No signals generated - This is why no trades!');
            }
        } else {
            console.log('⚠️ Signal endpoint not available - may need to check strategy execution directly');
        }

        // Final Results Summary
        console.log('\n\n🏆 TEST SUITE RESULTS');
        console.log('=====================');
        console.log(`✅ Tests Passed: ${passedTests}/${totalTests}`);
        console.log(`📊 Success Rate: ${Math.round((passedTests / totalTests) * 100)}%`);

        // Detailed Results Analysis
        if (passedTests === totalTests) {
            console.log('\n🎉 ALL TESTS PASSED! SYSTEM FULLY OPERATIONAL!');
            console.log('✅ Trade engine component fix: DEPLOYED & WORKING');
            console.log('✅ Elite recommendations strategy fix: DEPLOYED & WORKING');
            console.log('✅ Orchestrator status endpoint: WORKING');
            console.log('✅ All critical systems: OPERATIONAL');
            console.log('\n🚀 Your trading system is ready for 100+ trades/hour scalping!');

        } else if (passedTests >= totalTests * 0.8) {
            console.log(`\n✅ SYSTEM MOSTLY OPERATIONAL (${passedTests}/${totalTests} tests passed)`);
            console.log('Minor issues detected but core functionality working.');

        } else {
            console.log(`\n⚠️ SYSTEM ISSUES DETECTED (${passedTests}/${totalTests} tests passed)`);
            console.log('Some critical components may need attention.');
        }

        // Critical Fix Status
        console.log('\n🔧 CRITICAL FIXES STATUS:');
        const orchOk = document.querySelector('pre:last-of-type')?.textContent?.includes('Trade Engine Component ACTIVE: PASS') || false;
        const eliteOk = document.querySelector('pre:last-of-type')?.textContent?.includes('Using Real Trading Strategies: PASS') || false;

        console.log(`- Orchestrator Status Fix: ${orchOk ? '✅ WORKING' : '❌ NEEDS ATTENTION'}`);
        console.log(`- Elite Strategy Fix: ${eliteOk ? '✅ WORKING' : '❌ NEEDS ATTENTION'}`);

    } catch (error) {
        console.error('\n❌ TEST SUITE ERROR:', error);
        console.log('\nPlease try running individual tests or check network connection.');
    }
}

// Run the test suite
runComprehensiveTestSuite(); 