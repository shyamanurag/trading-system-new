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
    LOGIN: createEndpoint('/v1/auth/login'),
    REGISTER: createEndpoint('/v1/auth/register'),
    LOGOUT: createEndpoint('/v1/auth/logout'),
    REFRESH_TOKEN: createEndpoint('/v1/auth/refresh-token'),

    // User endpoints
    USERS: createEndpoint('/v1/users'),
    USER_PROFILE: createEndpoint('/v1/users/profile'),
    USER_PERFORMANCE: createEndpoint('/v1/users/performance'),

    // Trading endpoints
    TRADES: createEndpoint('/v1/trades'),
    POSITIONS: createEndpoint('/v1/positions'),
    ORDERS: createEndpoint('/v1/orders'),

    // Market data endpoints
    MARKET_DATA: createEndpoint('/v1/market-data'),
    SYMBOLS: createEndpoint('/v1/symbols'),

    // Strategy endpoints
    STRATEGIES: createEndpoint('/v1/strategies'),
    STRATEGY_PERFORMANCE: createEndpoint('/v1/strategies/performance'),

    // Dashboard endpoints
    DASHBOARD_SUMMARY: createEndpoint('/v1/dashboard/summary'),
    DAILY_PNL: createEndpoint('/v1/performance/daily-pnl'),
    RECOMMENDATIONS: createEndpoint('/v1/recommendations'),

    // Broker endpoints
    BROKER_CONNECT: createEndpoint('/v1/broker/connect'),
    BROKER_DISCONNECT: createEndpoint('/v1/broker/disconnect'),
    BROKER_STATUS: createEndpoint('/v1/broker/status'),

    // System endpoints
    SYSTEM_STATUS: createEndpoint('/v1/system/status'),
    SYSTEM_LOGS: createEndpoint('/v1/system/logs'),
    SYSTEM_METRICS: createEndpoint('/v1/system/metrics'),

    // WebSocket endpoints
    WS_MARKET_DATA: `${WS_BASE_URL}/ws/market-data`,
    WS_ORDERS: `${WS_BASE_URL}/ws/orders`,
    WS_POSITIONS: `${WS_BASE_URL}/ws/positions`,

    // Additional endpoints
    TICK_DATA: `${API_BASE_URL}/v1/tick-data`,
    ORDER_BOOK: `${API_BASE_URL}/v1/order-book`,
    ACCOUNT: `${API_BASE_URL}/v1/account`,
    HEALTH: `${API_BASE_URL}/health`,
    METRICS: `${API_BASE_URL}/metrics`,
    CONFIG: `${API_BASE_URL}/config`
};

export default API_ENDPOINTS; 