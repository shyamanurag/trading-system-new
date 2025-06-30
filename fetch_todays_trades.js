// 💰 COMPREHENSIVE TRADE TRANSACTION FETCHER
// Copy this ENTIRE script into your browser console (F12) to fetch today's trade data

const TRADE_API = {
    BASE_URL: 'https://algoauto-9gx56.ondigitalocean.app',

    // Helper function to make authenticated API calls
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

    // Fetch today's trade transactions from multiple endpoints
    async getTodaysTrades() {
        console.log(`%c🔍 Fetching Today's Trade Transactions...`, 'color: #2196F3; font-size: 16px; font-weight: bold');

        const today = new Date().toISOString().split('T')[0];
        console.log(`📅 Date Filter: ${today}`);

        const results = {};

        // 1. Try Dashboard Summary (Most comprehensive)
        console.log('%c1️⃣ Fetching Dashboard Summary...', 'color: #4CAF50; font-weight: bold');
        const dashboardResult = await this.fetchWithAuth('/api/v1/dashboard/dashboard/summary');
        if (dashboardResult.success) {
            results.dashboard = dashboardResult.data;
            console.log('%c✅ Dashboard Data:', 'color: #4CAF50', dashboardResult.data);

            // Extract trading metrics
            if (dashboardResult.data.autonomous_trading) {
                const trading = dashboardResult.data.autonomous_trading;
                console.log(`%c📊 Live Trading Status:
                🔥 Active: ${trading.is_active}
                📈 Total Trades: ${trading.total_trades}
                💰 Daily P&L: ₹${trading.daily_pnl}
                📍 Active Positions: ${trading.active_positions}
                🎯 Win Rate: ${trading.win_rate}%
                🕐 Session: ${trading.session_id || 'N/A'}`, 'color: #FF9800; font-weight: bold');
            }
        } else {
            console.error('❌ Dashboard fetch failed:', dashboardResult);
        }

        // 2. Try Performance Trades Endpoint
        console.log('%c2️⃣ Fetching Performance Trades...', 'color: #4CAF50; font-weight: bold');
        const performanceResult = await this.fetchWithAuth(`/api/v1/performance/trades?start_date=${today}&end_date=${today}`);
        if (performanceResult.success) {
            results.performance_trades = performanceResult.data;
            console.log('%c✅ Performance Trades:', 'color: #4CAF50', performanceResult.data);

            if (Array.isArray(performanceResult.data) && performanceResult.data.length > 0) {
                console.log(`%c📋 Trade Details:`, 'color: #9C27B0; font-weight: bold');
                performanceResult.data.forEach((trade, index) => {
                    console.log(`%c  ${index + 1}. ${trade.symbol} | ${trade.side} | Qty: ${trade.quantity} | Price: ₹${trade.price} | Time: ${trade.execution_time}`, 'color: #9C27B0');
                });
            }
        } else {
            console.error('❌ Performance trades fetch failed:', performanceResult);
        }

        // 3. Try General Trades Endpoint
        console.log('%c3️⃣ Fetching General Trades...', 'color: #4CAF50; font-weight: bold');
        const tradesResult = await this.fetchWithAuth('/api/v1/trades');
        if (tradesResult.success) {
            results.trades = tradesResult.data;
            console.log('%c✅ General Trades:', 'color: #4CAF50', tradesResult.data);
        } else {
            console.error('❌ General trades fetch failed:', tradesResult);
        }

        // 4. Try Live Trades Endpoint
        console.log('%c4️⃣ Fetching Live Trades...', 'color: #4CAF50; font-weight: bold');
        const liveTradesResult = await this.fetchWithAuth('/api/trades/live');
        if (liveTradesResult.success) {
            results.live_trades = liveTradesResult.data;
            console.log('%c✅ Live Trades:', 'color: #4CAF50', liveTradesResult.data);
        } else {
            console.error('❌ Live trades fetch failed:', liveTradesResult);
        }

        // 5. Try Trade Management Endpoint
        console.log('%c5️⃣ Fetching Trade Management Data...', 'color: #4CAF50; font-weight: bold');
        const tradeManagementResult = await this.fetchWithAuth('/api/v1/trade-management/');
        if (tradeManagementResult.success) {
            results.trade_management = tradeManagementResult.data;
            console.log('%c✅ Trade Management:', 'color: #4CAF50', tradeManagementResult.data);
        } else {
            console.error('❌ Trade management fetch failed:', tradeManagementResult);
        }

        // Summary Report
        console.log(`%c📊 === TODAY'S TRADING SUMMARY ===`, 'color: #E91E63; font-size: 18px; font-weight: bold; background: #FFF3E0; padding: 8px');

        let totalTrades = 0;
        let totalPnL = 0;
        let activePositions = 0;

        if (results.dashboard?.autonomous_trading) {
            const trading = results.dashboard.autonomous_trading;
            totalTrades = trading.total_trades || 0;
            totalPnL = trading.daily_pnl || 0;
            activePositions = trading.active_positions || 0;
        }

        console.log(`%c
        📅 Date: ${today}
        🎯 Total Trades: ${totalTrades}
        💰 Daily P&L: ₹${totalPnL.toFixed(2)}
        📍 Active Positions: ${activePositions}
        ⏰ Last Updated: ${new Date().toLocaleString()}
        `, 'color: #E91E63; font-size: 14px');

        return results;
    },

    // Fetch specific trade by ID
    async getTradeById(tradeId) {
        console.log(`%c🔍 Fetching Trade ID: ${tradeId}`, 'color: #2196F3; font-weight: bold');

        const result = await this.fetchWithAuth(`/api/v1/trades/${tradeId}`);
        if (result.success) {
            console.log('%c✅ Trade Details:', 'color: #4CAF50', result.data);
            return result.data;
        } else {
            console.error('❌ Trade fetch failed:', result);
            return null;
        }
    },

    // Fetch user-specific trades
    async getUserTrades(userId = 'AUTONOMOUS_TRADER') {
        console.log(`%c👤 Fetching Trades for User: ${userId}`, 'color: #2196F3; font-weight: bold');

        const result = await this.fetchWithAuth(`/api/v1/trades/users/${userId}`);
        if (result.success) {
            console.log('%c✅ User Trades:', 'color: #4CAF50', result.data);
            return result.data;
        } else {
            console.error('❌ User trades fetch failed:', result);
            return null;
        }
    },

    // Get positions (related to trades)
    async getPositions() {
        console.log(`%c📍 Fetching Current Positions...`, 'color: #2196F3; font-weight: bold');

        const result = await this.fetchWithAuth('/api/v1/positions');
        if (result.success) {
            console.log('%c✅ Positions:', 'color: #4CAF50', result.data);
            return result.data;
        } else {
            console.error('❌ Positions fetch failed:', result);
            return null;
        }
    },

    // Real-time trade monitoring
    async startTradeMonitoring(intervalSeconds = 30) {
        console.log(`%c🔄 Starting Real-time Trade Monitoring (${intervalSeconds}s intervals)`, 'color: #FF5722; font-weight: bold');

        const monitor = setInterval(async () => {
            console.log(`%c⏰ [${new Date().toLocaleTimeString()}] Updating trade data...`, 'color: #757575');
            await this.getTodaysTrades();
        }, intervalSeconds * 1000);

        console.log('%c✅ Monitoring started! Use TRADE_API.stopMonitoring() to stop.', 'color: #4CAF50');
        this.monitoringInterval = monitor;
        return monitor;
    },

    // Stop monitoring
    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
            console.log('%c🛑 Trade monitoring stopped.', 'color: #FF5722; font-weight: bold');
        }
    }
};

// Quick access functions
async function getTodaysTrades() {
    return await TRADE_API.getTodaysTrades();
}

async function getTradeById(id) {
    return await TRADE_API.getTradeById(id);
}

async function getPositions() {
    return await TRADE_API.getPositions();
}

async function startTradeMonitoring(seconds = 30) {
    return await TRADE_API.startTradeMonitoring(seconds);
}

function stopTradeMonitoring() {
    TRADE_API.stopMonitoring();
}

// Auto-show instructions when this section is loaded
console.log(`%c
🚀 === TRADE TRANSACTION FETCHING READY ===

Quick Commands:
• getTodaysTrades()                    - Fetch all today's trades
• getTradeById('trade_id')            - Get specific trade details  
• getPositions()                      - Get current positions
• startTradeMonitoring(30)            - Start real-time monitoring (30s)
• stopTradeMonitoring()               - Stop monitoring
• TRADE_API.getUserTrades('user_id')  - Get user-specific trades

Full API Object: TRADE_API.*

Example Usage:
// Get all today's trades
const trades = await getTodaysTrades();

// Start monitoring every 30 seconds
startTradeMonitoring(30);

// Get specific trade
const trade = await getTradeById('some-trade-id');

`, 'color: #4CAF50; font-size: 14px; font-weight: bold; background: #E8F5E8; padding: 10px');

// Auto-run to fetch today's trades immediately
console.log('%c🎯 Auto-fetching today\'s trades...', 'color: #2196F3; font-weight: bold');
getTodaysTrades(); 