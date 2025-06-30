// 💰 COMPREHENSIVE TRADE TRANSACTION FETCHER FOR BROWSER CONSOLE
// Copy this ENTIRE script into your browser console (F12) to fetch today's trade data

const TRADE_API = {
    BASE_URL: 'https://algoauto-9gx56.ondigitalocean.app',

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

    async getTodaysTrades() {
        console.log(`%c🔍 Fetching Today's Trade Transactions...`, 'color: #2196F3; font-size: 16px; font-weight: bold');

        const today = new Date().toISOString().split('T')[0];
        console.log(`📅 Date Filter: ${today}`);

        const results = {};

        // 1. Dashboard Summary - Main source of trade data  
        console.log('%c1️⃣ Fetching Dashboard Summary...', 'color: #4CAF50; font-weight: bold');
        const dashboardResult = await this.fetchWithAuth('/api/v1/dashboard/dashboard/summary');
        if (dashboardResult.success) {
            results.dashboard = dashboardResult.data;

            if (dashboardResult.data.autonomous_trading) {
                const trading = dashboardResult.data.autonomous_trading;
                console.log(`%c📊 Live Trading Status:
                🔥 Active: ${trading.is_active}
                📈 Total Trades: ${trading.total_trades}
                💰 Daily P&L: ₹${trading.daily_pnl}
                📍 Active Positions: ${trading.active_positions}
                🎯 Win Rate: ${trading.win_rate}%`, 'color: #FF9800; font-weight: bold');
            }
        }

        // 2. Performance Trades
        console.log('%c2️⃣ Fetching Performance Trades...', 'color: #4CAF50; font-weight: bold');
        const performanceResult = await this.fetchWithAuth(`/api/v1/performance/trades`);
        if (performanceResult.success) {
            results.performance_trades = performanceResult.data;
            if (Array.isArray(performanceResult.data) && performanceResult.data.length > 0) {
                console.log(`%c📋 Trade Details:`, 'color: #9C27B0; font-weight: bold');
                performanceResult.data.forEach((trade, index) => {
                    console.log(`%c  ${index + 1}. ${trade.symbol} | ${trade.side} | Qty: ${trade.quantity} | Price: ₹${trade.price}`, 'color: #9C27B0');
                });
            }
        }

        // 3. General Trades
        const tradesResult = await this.fetchWithAuth('/api/v1/trades');
        if (tradesResult.success) {
            results.trades = tradesResult.data;
        }

        // Summary Report
        console.log(`%c📊 === TODAY'S TRADING SUMMARY ===`, 'color: #E91E63; font-size: 18px; font-weight: bold');

        let totalTrades = 0;
        let totalPnL = 0;

        if (results.dashboard?.autonomous_trading) {
            totalTrades = results.dashboard.autonomous_trading.total_trades || 0;
            totalPnL = results.dashboard.autonomous_trading.daily_pnl || 0;
        }

        console.log(`%c
        📅 Date: ${today}
        🎯 Total Trades: ${totalTrades}
        💰 Daily P&L: ₹${totalPnL.toFixed(2)}
        ⏰ Last Updated: ${new Date().toLocaleString()}`, 'color: #E91E63; font-size: 14px');

        return results;
    }
};

// Quick functions
async function getTodaysTrades() {
    return await TRADE_API.getTodaysTrades();
}

console.log(`%c🚀 Trade Fetcher Ready! Use: getTodaysTrades()`, 'color: #4CAF50; font-size: 16px; font-weight: bold');
getTodaysTrades(); 