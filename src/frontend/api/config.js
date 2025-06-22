// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://algoauto-9gx56.ondigitalocean.app';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'wss://algoauto-9gx56.ondigitalocean.app';

// Ensure API_BASE_URL doesn't end with a slash
const normalizedApiUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;

// Add error handling wrapper
const createEndpoint = (path) => {
    // Ensure path starts with a slash
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    const fullUrl = `${normalizedApiUrl}${normalizedPath}`;

    // Debug logging
    console.log(`[API Config] Creating endpoint: ${normalizedPath} -> ${fullUrl}`);

    return {
        url: fullUrl,
        fallback: {
            success: false,
            error: 'Service temporarily unavailable',
            data: null
        }
    };
};

export const API_ENDPOINTS = {
    // Auth endpoints - IMPORTANT: These are at /auth, not /api/auth
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
    TICK_DATA: createEndpoint('/v1/tick-data'),
    ORDER_BOOK: createEndpoint('/v1/order-book'),
    ACCOUNT: createEndpoint('/v1/account'),
    HEALTH: createEndpoint('/health'),
    METRICS: createEndpoint('/metrics'),
    CONFIG: createEndpoint('/config')
};

// Debug logging
console.log('[API Config] Base URL:', normalizedApiUrl);
console.log('[API Config] Login URL:', API_ENDPOINTS.LOGIN.url);
console.log('[API Config] Health URL:', API_ENDPOINTS.HEALTH.url);

export default API_ENDPOINTS; 