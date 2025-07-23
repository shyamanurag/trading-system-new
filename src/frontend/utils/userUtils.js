/**
 * Unified User Management Utilities
 * Centralizes all user identification and management logic
 * Eliminates inconsistencies across frontend components
 */

import { USER_CONFIG, buildUserEndpoint, buildZerodhaEndpoint, getUserDisplayName, getUserIdentifier } from '../api/config.js';

/**
 * Standard User Object
 * All components should use this structure
 */
export const createStandardUser = (overrides = {}) => ({
    id: USER_CONFIG.PRIMARY_USER_ID,
    user_id: USER_CONFIG.PRIMARY_USER_ID,
    username: USER_CONFIG.DISPLAY_NAMES.MASTER,
    display_name: USER_CONFIG.DISPLAY_NAMES.MASTER,
    name: USER_CONFIG.DISPLAY_NAMES.MASTER,
    email: 'qsw899@trading-system.com',
    zerodha_client_id: USER_CONFIG.ZERODHA_USER_ID,
    zerodha_user_id: USER_CONFIG.ZERODHA_USER_ID,
    initial_capital: 10000000,  // 1 crore capital for live trading
    current_balance: 10000000,
    current_capital: 10000000,
    capital: 10000000,
    total_pnl: 0,
    total_trades: 0,
    win_rate: 0,
    open_trades: 0,
    is_active: true,
    trading_enabled: true,
    paper_trading: true,
    status: 'active',
    user_type: 'master',
    risk_tolerance: 'medium',
    created_at: new Date().toISOString(),
    joinDate: new Date().toISOString(),
    ...overrides
});

/**
 * Get user identifier for specific contexts
 */
export const getContextualUserId = (context) => {
    return getUserIdentifier(context);
};

/**
 * Get user display name for UI
 */
export const getContextualDisplayName = (userId) => {
    return getUserDisplayName(userId);
};

/**
 * Build API URLs with correct user parameters
 */
export const buildAPIUrl = (endpoint, context = 'database', additionalParams = {}) => {
    let url;

    if (context === 'zerodha') {
        url = buildZerodhaEndpoint(endpoint);
    } else {
        url = buildUserEndpoint(endpoint, context);
    }

    // Add additional parameters
    const paramString = Object.entries(additionalParams)
        .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
        .join('&');

    if (paramString) {
        const separator = url.includes('?') ? '&' : '?';
        url += separator + paramString;
    }

    return url;
};

/**
 * Standardize user data from different API responses
 */
export const standardizeUserData = (rawUserData, source = 'api') => {
    if (!rawUserData) return createStandardUser();

    // Handle different API response formats
    const standardized = {
        id: rawUserData.id || rawUserData.user_id || USER_CONFIG.PRIMARY_USER_ID,
        user_id: rawUserData.user_id || rawUserData.id || USER_CONFIG.PRIMARY_USER_ID,
        username: rawUserData.username || rawUserData.name || rawUserData.display_name || USER_CONFIG.DISPLAY_NAMES.MASTER,
        display_name: rawUserData.display_name || rawUserData.username || rawUserData.name || USER_CONFIG.DISPLAY_NAMES.MASTER,
        name: rawUserData.name || rawUserData.full_name || rawUserData.display_name || USER_CONFIG.DISPLAY_NAMES.MASTER,
        email: rawUserData.email || 'master@trading-system.com',
        zerodha_client_id: rawUserData.zerodha_client_id || rawUserData.client_id || USER_CONFIG.ZERODHA_USER_ID,
        zerodha_user_id: rawUserData.zerodha_user_id || USER_CONFIG.ZERODHA_USER_ID,

        // Financial data (updated for live trading amounts)
        initial_capital: rawUserData.initial_capital || rawUserData.capital || 10000000,
        current_balance: rawUserData.current_balance || rawUserData.current_capital || rawUserData.capital || 10000000,
        current_capital: rawUserData.current_capital || rawUserData.current_balance || rawUserData.capital || 10000000,
        capital: rawUserData.capital || rawUserData.current_capital || rawUserData.initial_capital || 10000000,

        // Trading stats
        total_pnl: rawUserData.total_pnl || rawUserData.totalPnL || 0,
        total_trades: rawUserData.total_trades || rawUserData.totalTrades || 0,
        win_rate: rawUserData.win_rate || rawUserData.winRate || 0,
        open_trades: rawUserData.open_trades || rawUserData.openTrades || 0,

        // Status flags
        is_active: rawUserData.is_active !== undefined ? rawUserData.is_active : true,
        trading_enabled: rawUserData.trading_enabled !== undefined ? rawUserData.trading_enabled : true,
        paper_trading: rawUserData.paper_trading !== undefined ? rawUserData.paper_trading : true,
        status: rawUserData.status || 'active',
        user_type: rawUserData.user_type || 'master',
        risk_tolerance: rawUserData.risk_tolerance || 'medium',

        // Timestamps
        created_at: rawUserData.created_at || rawUserData.joinDate || new Date().toISOString(),
        updated_at: rawUserData.updated_at || new Date().toISOString(),
        joinDate: rawUserData.joinDate || rawUserData.created_at || new Date().toISOString(),
        last_login: rawUserData.last_login || null
    };

    return standardized;
};

/**
 * Get default user for components that need immediate data
 */
export const getDefaultUser = () => {
    return createStandardUser();
};

/**
 * Check if a user ID represents the master/primary user
 */
export const isMasterUser = (userId) => {
    return userId === USER_CONFIG.PRIMARY_USER_ID ||
        userId === 'MASTER_USER_001' ||
        userId === USER_CONFIG.ZERODHA_USER_ID;
};

/**
 * Format user data for specific component needs
 */
export const formatUserForComponent = (userData, componentType = 'dashboard') => {
    const standardUser = standardizeUserData(userData);

    switch (componentType) {
        case 'table':
            return {
                id: standardUser.id,
                username: standardUser.username,
                email: standardUser.email,
                capital: standardUser.capital,
                totalTrades: standardUser.total_trades,
                winRate: standardUser.win_rate,
                status: standardUser.status,
                joinDate: standardUser.joinDate
            };

        case 'card':
            return {
                id: standardUser.id,
                name: standardUser.display_name,
                subtitle: standardUser.email,
                capital: standardUser.capital,
                pnl: standardUser.total_pnl,
                trades: standardUser.total_trades,
                status: standardUser.status
            };

        case 'zerodha':
            return {
                user_id: standardUser.zerodha_user_id,
                client_id: standardUser.zerodha_client_id,
                display_name: standardUser.display_name
            };

        default:
            return standardUser;
    }
};

/**
 * User validation helpers
 */
export const validateUserData = (userData) => {
    const errors = [];

    if (!userData.username || userData.username.trim() === '') {
        errors.push('Username is required');
    }

    if (!userData.email || !userData.email.includes('@')) {
        errors.push('Valid email is required');
    }

    if (userData.initial_capital !== undefined && userData.initial_capital < 0) {
        errors.push('Initial capital must be positive');
    }

    return {
        isValid: errors.length === 0,
        errors
    };
};

/**
 * Export all configuration for components that need it
 */
export { USER_CONFIG } from '../api/config.js';

