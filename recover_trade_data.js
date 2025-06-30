// 🆘 EMERGENCY TRADE DATA RECOVERY SCRIPT
// Run this in browser console to check if today's data can be recovered

const RECOVERY_API = {
    BASE_URL: 'https://algoauto-9gx56.ondigitalocean.app',
    TODAY: '20250630', // June 30, 2025

    async fetchWithAuth(endpoint, options = {}) {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(`${this.BASE_URL}${endpoint}`, {
                ...options,
                headers
            });

            const data = await response.json();
            return {
                success: response.ok,
                status: response.status,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    },

    // Try to recover trade data from multiple sources
    async emergencyDataRecovery() {
        console.log(`%c🆘 EMERGENCY TRADE DATA RECOVERY`, 'color: #FF0000; font-size: 18px; font-weight: bold; background: #FFEEEE; padding: 10px');
        console.log(`%c📅 Searching for data from: ${this.TODAY}`, 'color: #FF5722; font-weight: bold');

        const recovery_results = {};

        // 1. Check Redis for trade history
        console.log('%c1️⃣ Checking Redis Trade History...', 'color: #FF5722; font-weight: bold');
        const redisCheck = await this.checkRedisTradeHistory();
        recovery_results.redis = redisCheck;

        // 2. Check Database for trade records
        console.log('%c2️⃣ Checking Database Trade Records...', 'color: #FF5722; font-weight: bold');
        const dbCheck = await this.checkDatabaseTrades();
        recovery_results.database = dbCheck;

        // 3. Check System Logs for trade execution
        console.log('%c3️⃣ Checking System Logs...', 'color: #FF5722; font-weight: bold');
        const logsCheck = await this.checkSystemLogs();
        recovery_results.logs = logsCheck;

        // 4. Check if trading was actually active
        console.log('%c4️⃣ Checking Trading Activity Status...', 'color: #FF5722; font-weight: bold');
        const activityCheck = await this.checkTradingActivity();
        recovery_results.activity = activityCheck;

        // 5. Check deployment logs
        console.log('%c5️⃣ Checking Deployment History...', 'color: #FF5722; font-weight: bold');
        const deploymentCheck = await this.checkDeploymentHistory();
        recovery_results.deployment = deploymentCheck;

        // Generate recovery report
        this.generateRecoveryReport(recovery_results);

        return recovery_results;
    },

    async checkRedisTradeHistory() {
        try {
            // Try to access Redis trade history via API
            const endpoints = [
                `/api/v1/redis/trade_history:${this.TODAY}`,
                `/api/v1/debug/redis-keys`,
                `/api/v1/system/cache-status`
            ];

            for (const endpoint of endpoints) {
                const result = await this.fetchWithAuth(endpoint);
                if (result.success) {
                    console.log(`%c✅ Redis endpoint ${endpoint} accessible:`, 'color: #4CAF50', result.data);
                    return { found: true, data: result.data, source: endpoint };
                } else {
                    console.log(`%c❌ Redis endpoint ${endpoint} failed:`, 'color: #FF5722', result);
                }
            }

            return { found: false, message: 'No Redis endpoints accessible' };
        } catch (error) {
            return { found: false, error: error.message };
        }
    },

    async checkDatabaseTrades() {
        try {
            // Try database trade queries
            const today = new Date().toISOString().split('T')[0];
            const endpoints = [
                `/api/v1/performance/trades?start_date=${today}&end_date=${today}`,
                `/api/v1/db-health/trades/count`,
                `/api/v1/db-health/recent-activity`
            ];

            for (const endpoint of endpoints) {
                const result = await this.fetchWithAuth(endpoint);
                if (result.success) {
                    console.log(`%c✅ Database endpoint ${endpoint} accessible:`, 'color: #4CAF50', result.data);
                    return { found: true, data: result.data, source: endpoint };
                } else {
                    console.log(`%c❌ Database endpoint ${endpoint} failed:`, 'color: #FF5722', result);
                }
            }

            return { found: false, message: 'No database endpoints accessible' };
        } catch (error) {
            return { found: false, error: error.message };
        }
    },

    async checkSystemLogs() {
        try {
            const endpoints = [
                '/api/v1/system/logs',
                '/api/v1/monitoring/recent-events',
                '/api/v1/errors/recent'
            ];

            for (const endpoint of endpoints) {
                const result = await this.fetchWithAuth(endpoint);
                if (result.success && result.data) {
                    console.log(`%c✅ Log endpoint ${endpoint} accessible`, 'color: #4CAF50');

                    // Look for trade-related log entries
                    const logData = JSON.stringify(result.data).toLowerCase();
                    const tradeKeywords = ['trade', 'order', 'execution', 'buy', 'sell', 'position'];
                    const foundKeywords = tradeKeywords.filter(keyword => logData.includes(keyword));

                    if (foundKeywords.length > 0) {
                        console.log(`%c🔍 Found trade-related logs: ${foundKeywords.join(', ')}`, 'color: #FF9800');
                        return { found: true, keywords: foundKeywords, data: result.data, source: endpoint };
                    }
                }
            }

            return { found: false, message: 'No trade-related logs found' };
        } catch (error) {
            return { found: false, error: error.message };
        }
    },

    async checkTradingActivity() {
        try {
            // Check if autonomous trading was actually running
            const result = await this.fetchWithAuth('/api/v1/dashboard/dashboard/summary');
            if (result.success) {
                const data = result.data;
                console.log(`%c📊 Current Trading Status:`, 'color: #2196F3; font-weight: bold');
                console.log(`   🔥 Active: ${data.autonomous_trading?.is_active || false}`);
                console.log(`   📈 Total Trades: ${data.autonomous_trading?.total_trades || 0}`);
                console.log(`   💰 Daily P&L: ₹${data.autonomous_trading?.daily_pnl || 0}`);
                console.log(`   🕐 Session ID: ${data.autonomous_trading?.session_id || 'None'}`);

                return {
                    found: true,
                    was_active: data.autonomous_trading?.is_active || false,
                    total_trades: data.autonomous_trading?.total_trades || 0,
                    daily_pnl: data.autonomous_trading?.daily_pnl || 0,
                    session_id: data.autonomous_trading?.session_id
                };
            }

            return { found: false, message: 'Could not check trading activity' };
        } catch (error) {
            return { found: false, error: error.message };
        }
    },

    async checkDeploymentHistory() {
        try {
            // Check deployment-related endpoints
            const endpoints = [
                '/api/v1/system/status',
                '/health',
                '/metrics'
            ];

            const deploymentInfo = {};

            for (const endpoint of endpoints) {
                try {
                    const result = await this.fetchWithAuth(endpoint);
                    if (result.success) {
                        deploymentInfo[endpoint] = result.data;
                    }
                } catch (e) {
                    // Ignore individual endpoint failures
                }
            }

            return { found: Object.keys(deploymentInfo).length > 0, data: deploymentInfo };
        } catch (error) {
            return { found: false, error: error.message };
        }
    },

    generateRecoveryReport(results) {
        console.log(`%c📋 === RECOVERY REPORT ===`, 'color: #E91E63; font-size: 16px; font-weight: bold; background: #FFEEEE; padding: 10px');

        let dataFound = false;
        let tradesFound = 0;
        let pnlFound = 0;

        // Analyze results
        Object.entries(results).forEach(([source, result]) => {
            if (result.found) {
                dataFound = true;
                console.log(`%c✅ ${source.toUpperCase()}: Data found`, 'color: #4CAF50; font-weight: bold');

                if (result.total_trades) {
                    tradesFound = Math.max(tradesFound, result.total_trades);
                }
                if (result.daily_pnl) {
                    pnlFound = Math.max(pnlFound, Math.abs(result.daily_pnl));
                }
            } else {
                console.log(`%c❌ ${source.toUpperCase()}: No data`, 'color: #FF5722');
            }
        });

        // Final verdict
        console.log(`%c
🔍 RECOVERY ANALYSIS:
📊 Total Trades Found: ${tradesFound}
💰 Max P&L Found: ₹${pnlFound.toFixed(2)}
📅 Date: ${this.TODAY}
⏰ Search Time: ${new Date().toLocaleString()}

${dataFound ? '✅ SOME DATA RECOVERED' : '❌ NO DATA RECOVERED'}

${!dataFound ? `
⚠️  LIKELY CAUSES:
1. Trading was never actually active (mock components)
2. Data was stored in memory only (lost on restart)
3. Deployment wiped temporary storage
4. System was using paper trading mode without persistence

📋 NEXT STEPS:
1. Check if real trading was happening (vs. mock)
2. Implement proper data persistence
3. Set up frontend reporting
4. Prevent auto-deployments during trading hours
` : ''}
        `, 'color: #E91E63; font-size: 14px');
    }
};

// Quick recovery function
async function recoverTradeData() {
    return await RECOVERY_API.emergencyDataRecovery();
}

// Auto-run recovery
console.log('%c🆘 Starting Emergency Trade Data Recovery...', 'color: #FF0000; font-weight: bold');
recoverTradeData(); 