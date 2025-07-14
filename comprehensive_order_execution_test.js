/**
 * COMPREHENSIVE ORDER EXECUTION DIAGNOSTIC TEST SUITE
 * Run this in browser console to pinpoint the exact issue
 * 
 * Usage: Copy and paste this entire code into browser console
 */

class OrderExecutionDiagnostic {
    constructor() {
        this.baseUrl = 'https://algoauto-9gx56.ondigitalocean.app';
        this.results = {};
        this.issues = [];
        this.recommendations = [];
    }

    async runFullDiagnostic() {
        console.log('🔍 STARTING COMPREHENSIVE ORDER EXECUTION DIAGNOSTIC...\n');

        // Test 1: Frontend Authentication Status
        await this.testFrontendAuth();

        // Test 2: Redis Token Storage
        await this.testRedisTokenStorage();

        // Test 3: Environment Variables
        await this.testEnvironmentVariables();

        // Test 4: User Management
        await this.testUserManagement();

        // Test 5: System Status
        await this.testSystemStatus();

        // Test 6: Orchestrator Initialization
        await this.testOrchestratorInit();

        // Test 7: Signal Generation
        await this.testSignalGeneration();

        // Test 8: Order Execution Flow
        await this.testOrderExecutionFlow();

        // Test 9: Zerodha Connection
        await this.testZerodhaConnection();

        // Test 10: Trade Engine Status
        await this.testTradeEngineStatus();

        // Generate Report
        this.generateReport();
    }

    async testFrontendAuth() {
        console.log('📋 TEST 1: Frontend Authentication Status');
        try {
            const response = await fetch(`${this.baseUrl}/auth/zerodha/status`);
            const data = await response.json();

            this.results.frontendAuth = {
                success: data.success,
                authenticated: data.authenticated,
                user_id: data.user_id,
                profile_user_id: data.session?.profile?.user_id,
                token_available: data.session?.access_token,
                expires_at: data.session?.expires_at,
                valid: data.session?.valid
            };

            console.log('✅ Frontend Auth:', this.results.frontendAuth);

            if (!data.authenticated) {
                this.issues.push('❌ Frontend not authenticated');
                this.recommendations.push('💡 Run daily authentication via /auth/zerodha');
            }

            if (data.session?.profile?.user_id) {
                console.log(`🔑 Token should be stored in Redis as: zerodha:token:${data.session.profile.user_id}`);
            }

        } catch (error) {
            console.error('❌ Frontend Auth Test Failed:', error);
            this.issues.push('❌ Frontend authentication endpoint unreachable');
        }
        console.log('');
    }

    async testRedisTokenStorage() {
        console.log('📋 TEST 2: Redis Token Storage (via API)');
        try {
            // Try to get system info that might show Redis status
            const response = await fetch(`${this.baseUrl}/api/v1/system/redis-status`);
            if (response.ok) {
                const data = await response.json();
                this.results.redisStatus = data;
                console.log('✅ Redis Status:', data);
            } else {
                console.log('ℹ️ Redis status endpoint not available');
            }

            // Check if we can infer Redis token storage from logs
            const logsResponse = await fetch(`${this.baseUrl}/api/v1/system/logs`);
            if (logsResponse.ok) {
                const logs = await logsResponse.text();
                const tokenLogs = logs.split('\n').filter(line =>
                    line.includes('zerodha:token') ||
                    line.includes('Found Zerodha token') ||
                    line.includes('Redis')
                ).slice(-10);

                if (tokenLogs.length > 0) {
                    console.log('🔍 Recent Redis/Token logs:');
                    tokenLogs.forEach(log => console.log('  ', log));
                }
            }

        } catch (error) {
            console.error('❌ Redis Token Storage Test Failed:', error);
        }
        console.log('');
    }

    async testEnvironmentVariables() {
        console.log('📋 TEST 3: Environment Variables Check');
        try {
            // Check autonomous status for env var hints
            const response = await fetch(`${this.baseUrl}/api/v1/autonomous/status`);
            const data = await response.json();

            this.results.envVars = {
                active_user_from_system: data.data?.active_user_id || 'Not found',
                system_ready: data.data?.system_ready,
                environment_hints: {}
            };

            console.log('✅ Environment Variable Hints:', this.results.envVars);

            // Check if ACTIVE_USER_ID is working
            if (!data.data?.active_user_id || data.data.active_user_id === 'system') {
                this.issues.push('❌ ACTIVE_USER_ID environment variable not working');
                this.recommendations.push('💡 Check if ACTIVE_USER_ID=PAPER_TRADER_MAIN is set in deployment');
            }

        } catch (error) {
            console.error('❌ Environment Variables Test Failed:', error);
        }
        console.log('');
    }

    async testUserManagement() {
        console.log('📋 TEST 4: User Management');
        try {
            // Check broker users
            const brokerResponse = await fetch(`${this.baseUrl}/api/v1/control/users/broker`);
            const brokerData = await brokerResponse.json();

            // Check current user
            const userResponse = await fetch(`${this.baseUrl}/api/v1/users/current`);
            const userData = await userResponse.json();

            this.results.userManagement = {
                broker_users: brokerData,
                current_user: userData,
                paper_trader_main_exists: brokerData.users?.includes('PAPER_TRADER_MAIN'),
                paper_trader_001_exists: brokerData.users?.includes('PAPER_TRADER_001')
            };

            console.log('✅ User Management:', this.results.userManagement);

            if (!brokerData.users?.includes('PAPER_TRADER_MAIN')) {
                this.issues.push('❌ PAPER_TRADER_MAIN user not found');
                this.recommendations.push('💡 Run setup_paper_trading_user.py to create required users');
            }

        } catch (error) {
            console.error('❌ User Management Test Failed:', error);
        }
        console.log('');
    }

    async testSystemStatus() {
        console.log('📋 TEST 5: System Status');
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/system/status`);
            const data = await response.json();

            this.results.systemStatus = {
                components: data.components || {},
                zerodha_status: data.zerodha_status || 'unknown',
                system_ready: data.system_ready,
                deployment_id: data.deployment_id
            };

            console.log('✅ System Status:', this.results.systemStatus);

            if (!data.system_ready) {
                this.issues.push('❌ System not ready');
                this.recommendations.push('💡 Wait for system initialization or check deployment logs');
            }

        } catch (error) {
            console.error('❌ System Status Test Failed:', error);
        }
        console.log('');
    }

    async testOrchestratorInit() {
        console.log('📋 TEST 6: Orchestrator Initialization');
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/autonomous/status`);
            const data = await response.json();

            this.results.orchestrator = {
                is_active: data.data?.is_active,
                system_ready: data.data?.system_ready,
                active_strategies: data.data?.active_strategies || [],
                total_trades: data.data?.total_trades || 0,
                session_id: data.data?.session_id,
                last_heartbeat: data.data?.last_heartbeat
            };

            console.log('✅ Orchestrator Status:', this.results.orchestrator);

            if (!data.data?.is_active) {
                this.issues.push('❌ Orchestrator not active');
                this.recommendations.push('💡 Call /api/v1/autonomous/force-activate to activate');
            }

            if (data.data?.total_trades === 0) {
                this.issues.push('⚠️ Zero trades executed');
                this.recommendations.push('💡 This is the main issue - orders not executing');
            }

        } catch (error) {
            console.error('❌ Orchestrator Test Failed:', error);
        }
        console.log('');
    }

    async testSignalGeneration() {
        console.log('📋 TEST 7: Signal Generation');
        try {
            // Check recent logs for signal generation
            const response = await fetch(`${this.baseUrl}/api/v1/system/logs`);
            const logs = await response.text();

            const signalLogs = logs.split('\n').filter(line =>
                line.includes('SIGNAL COLLECTED') ||
                line.includes('signals through trade engine') ||
                line.includes('signals for batch processing')
            ).slice(-5);

            this.results.signalGeneration = {
                recent_signals: signalLogs.length,
                signal_logs: signalLogs
            };

            console.log('✅ Signal Generation:', this.results.signalGeneration);

            if (signalLogs.length === 0) {
                this.issues.push('❌ No recent signals found');
                this.recommendations.push('💡 Check if strategies are running and market is open');
            } else {
                console.log('🔍 Recent Signal Logs:');
                signalLogs.forEach(log => console.log('  ', log));
            }

        } catch (error) {
            console.error('❌ Signal Generation Test Failed:', error);
        }
        console.log('');
    }

    async testOrderExecutionFlow() {
        console.log('📋 TEST 8: Order Execution Flow');
        try {
            // Check recent logs for order execution
            const response = await fetch(`${this.baseUrl}/api/v1/system/logs`);
            const logs = await response.text();

            const orderLogs = logs.split('\n').filter(line =>
                line.includes('place order') ||
                line.includes('order placed') ||
                line.includes('order rejected') ||
                line.includes('Failed to place order') ||
                line.includes('user system')
            ).slice(-10);

            this.results.orderExecution = {
                recent_order_attempts: orderLogs.length,
                order_logs: orderLogs
            };

            console.log('✅ Order Execution Flow:', this.results.orderExecution);

            if (orderLogs.length > 0) {
                console.log('🔍 Recent Order Logs:');
                orderLogs.forEach(log => console.log('  ', log));

                // Check for specific issues
                const systemUserLogs = orderLogs.filter(log => log.includes('user system'));
                if (systemUserLogs.length > 0) {
                    this.issues.push('❌ Orders still using "user system" instead of ACTIVE_USER_ID');
                    this.recommendations.push('💡 ACTIVE_USER_ID environment variable not working');
                }
            }

        } catch (error) {
            console.error('❌ Order Execution Test Failed:', error);
        }
        console.log('');
    }

    async testZerodhaConnection() {
        console.log('📋 TEST 9: Zerodha Connection');
        try {
            // Check recent logs for Zerodha connection issues
            const response = await fetch(`${this.baseUrl}/api/v1/system/logs`);
            const logs = await response.text();

            const zerodhaLogs = logs.split('\n').filter(line =>
                line.includes('Zerodha') ||
                line.includes('Invalid `api_key` or `access_token`') ||
                line.includes('Found Zerodha token') ||
                line.includes('LIVE mode') ||
                line.includes('mock mode')
            ).slice(-10);

            this.results.zerodhaConnection = {
                recent_zerodha_logs: zerodhaLogs.length,
                zerodha_logs: zerodhaLogs
            };

            console.log('✅ Zerodha Connection:', this.results.zerodhaConnection);

            if (zerodhaLogs.length > 0) {
                console.log('🔍 Recent Zerodha Logs:');
                zerodhaLogs.forEach(log => console.log('  ', log));

                // Check for specific issues
                const invalidTokenLogs = zerodhaLogs.filter(log => log.includes('Invalid `api_key` or `access_token`'));
                if (invalidTokenLogs.length > 0) {
                    this.issues.push('❌ Zerodha token retrieval failing');
                    this.recommendations.push('💡 Orchestrator not retrieving token from Redis properly');
                }

                const mockModeLogs = zerodhaLogs.filter(log => log.includes('mock mode'));
                if (mockModeLogs.length > 0) {
                    this.issues.push('❌ Zerodha running in mock mode');
                    this.recommendations.push('💡 Token not found, should run in LIVE mode');
                }
            }

        } catch (error) {
            console.error('❌ Zerodha Connection Test Failed:', error);
        }
        console.log('');
    }

    async testTradeEngineStatus() {
        console.log('📋 TEST 10: Trade Engine Status');
        try {
            // Try to get trade engine specific status
            const response = await fetch(`${this.baseUrl}/api/v1/trades/status`);
            if (response.ok) {
                const data = await response.json();
                this.results.tradeEngine = data;
                console.log('✅ Trade Engine Status:', data);
            } else {
                console.log('ℹ️ Trade engine status endpoint not available');
            }

            // Check for trade engine logs
            const logsResponse = await fetch(`${this.baseUrl}/api/v1/system/logs`);
            const logs = await logsResponse.text();

            const tradeEngineLogs = logs.split('\n').filter(line =>
                line.includes('trade_engine') ||
                line.includes('TradeEngine') ||
                line.includes('batch processing')
            ).slice(-5);

            if (tradeEngineLogs.length > 0) {
                console.log('🔍 Recent Trade Engine Logs:');
                tradeEngineLogs.forEach(log => console.log('  ', log));
            }

        } catch (error) {
            console.error('❌ Trade Engine Test Failed:', error);
        }
        console.log('');
    }

    generateReport() {
        console.log('📊 COMPREHENSIVE DIAGNOSTIC REPORT');
        console.log('=====================================\n');

        // Summary
        console.log('🎯 SUMMARY:');
        console.log(`Total Issues Found: ${this.issues.length}`);
        console.log(`Total Recommendations: ${this.recommendations.length}\n`);

        // Issues
        if (this.issues.length > 0) {
            console.log('❌ ISSUES FOUND:');
            this.issues.forEach((issue, index) => {
                console.log(`${index + 1}. ${issue}`);
            });
            console.log('');
        }

        // Recommendations
        if (this.recommendations.length > 0) {
            console.log('💡 RECOMMENDATIONS:');
            this.recommendations.forEach((rec, index) => {
                console.log(`${index + 1}. ${rec}`);
            });
            console.log('');
        }

        // Key Findings
        console.log('🔍 KEY FINDINGS:');

        if (this.results.frontendAuth?.authenticated) {
            console.log('✅ Frontend authentication is working');
            console.log(`   Token stored as: zerodha:token:${this.results.frontendAuth.profile_user_id}`);
        }

        if (this.results.orchestrator?.total_trades === 0) {
            console.log('❌ MAIN ISSUE: Zero trades executed');
            console.log('   This indicates orders are not being placed successfully');
        }

        if (this.results.envVars?.active_user_from_system === 'system') {
            console.log('❌ ACTIVE_USER_ID not working - still using "system"');
        }

        console.log('\n🔧 NEXT STEPS:');
        console.log('1. Fix the issues listed above in order of priority');
        console.log('2. Re-run this diagnostic after each fix');
        console.log('3. Monitor logs for "✅ Found Zerodha token" and "🔄 LIVE mode" messages');
        console.log('4. Check for increasing total_trades count');

        console.log('\n📋 FULL RESULTS OBJECT:');
        console.log('Access via: diagnostic.results');
        console.log(this.results);
    }

    // Helper method to force activate trading
    async forceActivateTrading() {
        console.log('🚀 Force Activating Trading...');
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/autonomous/force-activate`, {
                method: 'POST'
            });
            const data = await response.json();
            console.log('✅ Force Activation Result:', data);
            return data;
        } catch (error) {
            console.error('❌ Force Activation Failed:', error);
            return null;
        }
    }

    // Helper method to check live logs
    async watchLiveLogs(duration = 30000) {
        console.log(`👁️ Watching live logs for ${duration / 1000} seconds...`);
        const startTime = Date.now();

        const checkLogs = async () => {
            try {
                const response = await fetch(`${this.baseUrl}/api/v1/system/logs`);
                const logs = await response.text();
                const recentLogs = logs.split('\n').slice(-5);

                console.log('📝 Recent logs:');
                recentLogs.forEach(log => {
                    if (log.trim()) console.log('  ', log);
                });
                console.log('---');

            } catch (error) {
                console.error('Error fetching logs:', error);
            }
        };

        const interval = setInterval(checkLogs, 5000);

        setTimeout(() => {
            clearInterval(interval);
            console.log('👁️ Live log watching stopped');
        }, duration);
    }
}

// Auto-run the diagnostic
const diagnostic = new OrderExecutionDiagnostic();

console.log('🎯 COMPREHENSIVE ORDER EXECUTION DIAGNOSTIC SUITE');
console.log('================================================');
console.log('');
console.log('Usage:');
console.log('  diagnostic.runFullDiagnostic()     - Run complete diagnostic');
console.log('  diagnostic.forceActivateTrading()  - Force activate trading');
console.log('  diagnostic.watchLiveLogs(30000)    - Watch logs for 30 seconds');
console.log('  diagnostic.results                 - View all test results');
console.log('');
console.log('🚀 Starting automatic diagnostic in 2 seconds...');
console.log('');

setTimeout(() => {
    diagnostic.runFullDiagnostic();
}, 2000);

// Make diagnostic available globally
window.diagnostic = diagnostic; 