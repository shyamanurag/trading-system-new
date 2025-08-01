/**
 * Real Data Service - Provides genuine dynamic data with NO hardcoded fallbacks
 * This service ensures all frontend components use only real data from working APIs
 */

import fetchWithAuth from '../api/fetchWithAuth';

class RealDataService {
    constructor() {
        this.cache = {};
        this.cacheTimeout = 30000; // 30 seconds cache
    }

    /**
     * Get real capital from various sources - NO HARDCODED FALLBACKS
     */
    async getRealCapital() {
        try {
            // Try autonomous status first (most reliable)
            const autonomousRes = await fetchWithAuth('/api/v1/autonomous/status');
            if (autonomousRes.ok) {
                const data = await autonomousRes.json();
                if (data.success && data.data) {
                    return data.data.capital || data.data.aum || 0;
                }
            }

            // Try users endpoint
            const usersRes = await fetchWithAuth('/api/v1/users');
            if (usersRes.ok) {
                const userData = await usersRes.json();
                if (userData.success && userData.data && userData.data.user_metrics) {
                    const users = Object.values(userData.data.user_metrics);
                    if (users.length > 0) {
                        return users[0].initial_capital || users[0].capital || 0;
                    }
                }
            }

            // Try positions endpoint to calculate from current positions
            const positionsRes = await fetchWithAuth('/api/v1/positions');
            if (positionsRes.ok) {
                const posData = await positionsRes.json();
                if (posData.success && posData.positions && posData.positions.length > 0) {
                    // Calculate based on position values
                    const totalInvested = posData.positions.reduce((sum, pos) => {
                        return sum + (pos.average_price * Math.abs(pos.quantity));
                    }, 0);
                    return totalInvested + Math.abs(posData.total_pnl || 0);
                }
            }

            return 0; // NO HARDCODED FALLBACK - return 0 if no real data
        } catch (error) {
            console.error('Error fetching real capital:', error);
            return 0; // NO HARDCODED FALLBACK
        }
    }

    /**
     * Get real trading metrics - NO MOCK DATA
     */
    async getRealTradingMetrics() {
        try {
            const autonomousRes = await fetchWithAuth('/api/v1/autonomous/status');
            if (autonomousRes.ok) {
                const data = await autonomousRes.json();
                if (data.success && data.data) {
                    return {
                        dailyPnL: data.data.daily_pnl || 0,
                        totalTrades: data.data.total_trades || 0,
                        activePositions: data.data.active_positions || 0,
                        isActive: data.data.is_active || false,
                        winRate: data.data.win_rate || 0,
                        capital: data.data.capital || data.data.aum || 0
                    };
                }
            }
            
            return {
                dailyPnL: 0,
                totalTrades: 0,
                activePositions: 0,
                isActive: false,
                winRate: 0,
                capital: 0
            };
        } catch (error) {
            console.error('Error fetching real trading metrics:', error);
            return {
                dailyPnL: 0,
                totalTrades: 0,
                activePositions: 0,
                isActive: false,
                winRate: 0,
                capital: 0
            };
        }
    }

    /**
     * Get real positions data - NO MOCK POSITIONS
     */
    async getRealPositions() {
        try {
            const positionsRes = await fetchWithAuth('/api/v1/positions');
            if (positionsRes.ok) {
                const data = await positionsRes.json();
                if (data.success) {
                    return {
                        positions: data.positions || [],
                        totalPnL: data.total_pnl || 0,
                        count: data.count || 0
                    };
                }
            }
            
            return {
                positions: [],
                totalPnL: 0,
                count: 0
            };
        } catch (error) {
            console.error('Error fetching real positions:', error);
            return {
                positions: [],
                totalPnL: 0,
                count: 0
            };
        }
    }

    /**
     * Get real user data - NO FAKE USERS
     */
    async getRealUsers() {
        try {
            const usersRes = await fetchWithAuth('/api/v1/users');
            if (usersRes.ok) {
                const data = await usersRes.json();
                if (data.success && data.data) {
                    return data.data.user_metrics || {};
                }
            }
            
            return {};
        } catch (error) {
            console.error('Error fetching real users:', error);
            return {};
        }
    }

    /**
     * Comprehensive real data fetch for dashboard components
     */
    async getComprehensiveRealData() {
        try {
            const [capital, metrics, positions, users] = await Promise.all([
                this.getRealCapital(),
                this.getRealTradingMetrics(),
                this.getRealPositions(),
                this.getRealUsers()
            ]);

            return {
                capital,
                metrics,
                positions,
                users,
                // Derived metrics
                totalAUM: capital + metrics.dailyPnL,
                activeUsers: Object.keys(users).length || (metrics.isActive ? 1 : 0),
                portfolioValue: capital + positions.totalPnL
            };
        } catch (error) {
            console.error('Error fetching comprehensive real data:', error);
            return {
                capital: 0,
                metrics: { dailyPnL: 0, totalTrades: 0, activePositions: 0, isActive: false, winRate: 0, capital: 0 },
                positions: { positions: [], totalPnL: 0, count: 0 },
                users: {},
                totalAUM: 0,
                activeUsers: 0,
                portfolioValue: 0
            };
        }
    }
}

// Export singleton instance
export default new RealDataService();