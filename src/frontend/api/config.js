// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Add error handling wrapper
const createEndpoint = (path) => {
    return {
        url: `${API_BASE_URL}${path}`,
        fallback: {
            success: false,
            error: 'Service temporarily unavailable',
            data: null
        }
    };
};

export const API_ENDPOINTS = {
    // Auth endpoints
    LOGIN: createEndpoint('/api/v1/auth/login'),
    REGISTER: createEndpoint('/api/v1/auth/register'),
    LOGOUT: createEndpoint('/api/v1/auth/logout'),
    REFRESH_TOKEN: createEndpoint('/api/v1/auth/refresh-token'),

    // User endpoints
    USERS: createEndpoint('/api/v1/users'),
    USER_PROFILE: createEndpoint('/api/v1/users/profile'),
    USER_PERFORMANCE: createEndpoint('/api/v1/users/performance'),

    // Trading endpoints
    TRADES: createEndpoint('/api/v1/trades'),
    POSITIONS: createEndpoint('/api/v1/positions'),
    ORDERS: createEndpoint('/api/v1/orders'),

    // Market data endpoints
    MARKET_DATA: createEndpoint('/api/v1/market-data'),
    SYMBOLS: createEndpoint('/api/v1/symbols'),

    // Strategy endpoints
    STRATEGIES: createEndpoint('/api/v1/strategies'),
    STRATEGY_PERFORMANCE: createEndpoint('/api/v1/strategies/performance'),

    // Dashboard endpoints
    DASHBOARD_SUMMARY: createEndpoint('/api/v1/dashboard/summary'),
    DAILY_PNL: createEndpoint('/api/v1/performance/daily-pnl'),
    RECOMMENDATIONS: createEndpoint('/api/v1/recommendations'),

    // Broker endpoints
    BROKER_CONNECT: createEndpoint('/api/v1/broker/connect'),
    BROKER_DISCONNECT: createEndpoint('/api/v1/broker/disconnect'),
    BROKER_STATUS: createEndpoint('/api/v1/broker/status'),

    // System endpoints
    SYSTEM_STATUS: createEndpoint('/api/v1/system/status'),
    SYSTEM_LOGS: createEndpoint('/api/v1/system/logs'),
    SYSTEM_METRICS: createEndpoint('/api/v1/system/metrics')
};

export default API_ENDPOINTS; 