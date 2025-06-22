// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://algoauto-9gx56.ondigitalocean.app';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'wss://algoauto-9gx56.ondigitalocean.app';

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
    // Auth endpoints - Updated to match backend routes
    LOGIN: createEndpoint('/auth/login'),
    REGISTER: createEndpoint('/auth/register'),
    LOGOUT: createEndpoint('/auth/logout'),
    REFRESH_TOKEN: createEndpoint('/auth/refresh-token'),
    ME: createEndpoint('/auth/me'),

    // User endpoints - These use /api/v1/users prefix
    USERS: createEndpoint('/api/v1/users'),
    USER_PROFILE: createEndpoint('/api/v1/users/profile'),
    USER_PERFORMANCE: createEndpoint('/api/v1/users/performance'),
    USER_CURRENT: createEndpoint('/api/v1/users/current'),

    // Trading endpoints
    TRADES: createEndpoint('/v1/trades'),
    POSITIONS: createEndpoint('/v1/positions'),
    ORDERS: createEndpoint('/v1/orders'),

    // Market data endpoints - These use /api/market prefix
    MARKET_INDICES: createEndpoint('/api/market/indices'),
    MARKET_STATUS: createEndpoint('/api/market/market-status'),
    MARKET_DATA: createEndpoint('/api/market/data'),
    SYMBOLS: createEndpoint('/api/market/symbols'),

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

// Debug logging
console.log('[API Config] Base URL:', API_BASE_URL);
console.log('[API Config] Login URL:', API_ENDPOINTS.LOGIN.url);

export default API_ENDPOINTS; 