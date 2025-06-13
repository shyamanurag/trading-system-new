// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

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
    LOGIN: createEndpoint('/api/auth/login'),
    REGISTER: createEndpoint('/api/auth/register'),
    LOGOUT: createEndpoint('/api/auth/logout'),
    REFRESH_TOKEN: createEndpoint('/api/auth/refresh-token'),

    // User endpoints
    USERS: createEndpoint('/api/users'),
    USER_PROFILE: createEndpoint('/api/users/profile'),
    USER_PERFORMANCE: createEndpoint('/api/users/performance'),

    // Trading endpoints
    TRADES: createEndpoint('/api/trades'),
    POSITIONS: createEndpoint('/api/positions'),
    ORDERS: createEndpoint('/api/orders'),

    // Market data endpoints
    MARKET_DATA: createEndpoint('/api/market-data'),
    SYMBOLS: createEndpoint('/api/symbols'),

    // Strategy endpoints
    STRATEGIES: createEndpoint('/api/strategies'),
    STRATEGY_PERFORMANCE: createEndpoint('/api/strategies/performance'),

    // Dashboard endpoints
    DASHBOARD_SUMMARY: createEndpoint('/api/dashboard/summary'),
    DAILY_PNL: createEndpoint('/api/performance/daily-pnl'),
    RECOMMENDATIONS: createEndpoint('/api/recommendations'),

    // Broker endpoints
    BROKER_CONNECT: createEndpoint('/api/broker/connect'),
    BROKER_DISCONNECT: createEndpoint('/api/broker/disconnect'),
    BROKER_STATUS: createEndpoint('/api/broker/status'),

    // System endpoints
    SYSTEM_STATUS: createEndpoint('/api/system/status'),
    SYSTEM_LOGS: createEndpoint('/api/system/logs'),
    SYSTEM_METRICS: createEndpoint('/api/system/metrics'),

    // WebSocket endpoints
    WS_MARKET_DATA: `${WS_BASE_URL}/ws/market-data`,
    WS_ORDERS: `${WS_BASE_URL}/ws/orders`,
    WS_POSITIONS: `${WS_BASE_URL}/ws/positions`,

    // Additional endpoints
    TICK_DATA: `${API_BASE_URL}/api/tick-data`,
    ORDER_BOOK: `${API_BASE_URL}/api/order-book`,
    ACCOUNT: `${API_BASE_URL}/api/account`,
    HEALTH: `${API_BASE_URL}/health`,
    METRICS: `${API_BASE_URL}/metrics`,
    CONFIG: `${API_BASE_URL}/api/config`
};

export default API_ENDPOINTS; 