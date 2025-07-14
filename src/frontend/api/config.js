// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://algoauto-9gx56.ondigitalocean.app';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'wss://algoauto-9gx56.ondigitalocean.app/ws';

// Ensure API_BASE_URL doesn't end with a slash
const normalizedApiUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;

// Add error handling wrapper
const createEndpoint = (path, requiresTrailingSlash = false) => {
    // Ensure path starts with a slash
    let normalizedPath = path.startsWith('/') ? path : `/${path}`;

    // Add trailing slash if required
    if (requiresTrailingSlash && !normalizedPath.endsWith('/')) {
        normalizedPath += '/';
    }

    const fullUrl = `${normalizedApiUrl}${normalizedPath}`;

    // Debug logging
    // console.log(`[API Config] Creating endpoint: ${normalizedPath} -> ${fullUrl}`);

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
    // Auth endpoints - FIXED: Use /api/auth path to match backend
    LOGIN: createEndpoint('/api/auth/login'),
    REGISTER: createEndpoint('/api/auth/register'),
    LOGOUT: createEndpoint('/api/auth/logout'),
    REFRESH_TOKEN: createEndpoint('/api/auth/refresh-token'),
    USER_PROFILE: createEndpoint('/api/auth/me'),

    // User endpoints - These use /api/v1/users prefix - FIXED: Added trailing slash
    USERS: createEndpoint('/api/v1/users/', true),
    USER_PERFORMANCE: createEndpoint('/api/v1/users/performance'),
    USER_CURRENT: createEndpoint('/api/v1/users/current'),

    // Broker user management
    BROKER_USERS: createEndpoint('/api/v1/control/users/broker'),

    // Trading endpoints - FIXED: Added /api prefix and trailing slashes
    TRADES: createEndpoint('/api/v1/trades', true),
    POSITIONS: createEndpoint('/api/v1/positions', true),
    ORDERS: createEndpoint('/api/v1/orders', true),

    // Trading control endpoints
    TRADING_CONTROL: createEndpoint('/api/v1/control/trading/control'),
    TRADING_STATUS: createEndpoint('/api/v1/control/trading/status'),

    // Market data endpoints - These use /api/market prefix
    MARKET_INDICES: createEndpoint('/api/market/indices'),
    MARKET_STATUS: createEndpoint('/api/market/market-status'),
    MARKET_DATA: createEndpoint('/api/v1/market-data/NIFTY'),
    SYMBOLS: createEndpoint('/api/market/symbols'),

    // Strategy endpoints - FIXED: Added /api prefix
    STRATEGIES: createEndpoint('/api/v1/strategies'),
    STRATEGY_PERFORMANCE: createEndpoint('/api/v1/strategies/performance'),

    // Dashboard endpoints - FIXED: Added /api prefix
    DASHBOARD_SUMMARY: createEndpoint('/api/v1/dashboard/dashboard/summary'),
    DAILY_PNL: createEndpoint('/api/v1/monitoring/daily-pnl'),
    RECOMMENDATIONS: createEndpoint('/api/v1/elite', true),
    ELITE_RECOMMENDATIONS: createEndpoint('/api/v1/elite', true),
    DASHBOARD_DATA: createEndpoint('/api/v1/dashboard/data'),

    // Broker endpoints - FIXED: Added /api prefix
    BROKER_CONNECT: createEndpoint('/api/v1/broker/connect'),
    BROKER_DISCONNECT: createEndpoint('/api/v1/broker/disconnect'),
    BROKER_STATUS: createEndpoint('/api/v1/broker/status'),

    // System endpoints - FIXED: Added /api prefix
    SYSTEM_STATUS: createEndpoint('/api/v1/system/status'),
    SYSTEM_LOGS: createEndpoint('/api/v1/system/logs'),
    SYSTEM_METRICS: createEndpoint('/api/v1/system/metrics'),

    // Risk management endpoints - NEW
    RISK_METRICS: createEndpoint('/api/v1/risk/metrics'),
    RISK_LIMITS: createEndpoint('/api/v1/risk/limits'),
    RISK_ALERTS: createEndpoint('/api/v1/risk/alerts'),

    // Autonomous trading endpoints - NEW
    AUTONOMOUS_STATUS: createEndpoint('/api/v1/autonomous/status'),
    AUTONOMOUS_START: createEndpoint('/api/v1/autonomous/start'),
    AUTONOMOUS_STOP: createEndpoint('/api/v1/autonomous/stop'),
    AUTONOMOUS_CONTROL: createEndpoint('/api/v1/autonomous/control'),
    AUTONOMOUS_DATA: createEndpoint('/api/v1/autonomous/status'),

    // WebSocket endpoints - FIXED: Using single /ws endpoint
    WS_ENDPOINT: `${WS_BASE_URL}/ws`,
    // Legacy WebSocket endpoints for backward compatibility
    WS_MARKET_DATA: `${WS_BASE_URL}/ws`,
    WS_ORDERS: `${WS_BASE_URL}/ws`,
    WS_POSITIONS: `${WS_BASE_URL}/ws`,

    // Additional endpoints - FIXED: Added /api prefix where needed
    TICK_DATA: createEndpoint('/api/v1/tick-data'),
    ORDER_BOOK: createEndpoint('/api/v1/order-book'),
    ACCOUNT: createEndpoint('/api/v1/account'),
    HEALTH: createEndpoint('/health'),
    HEALTH_READY_JSON: createEndpoint('/health/ready/json'),
    METRICS: createEndpoint('/metrics'),
    CONFIG: createEndpoint('/config'),

    // Zerodha Manual Auth endpoints
    ZERODHA_AUTH_URL: createEndpoint('/auth/zerodha/auth-url'),
    ZERODHA_AUTH_STATUS: createEndpoint('/auth/zerodha/status'),
    ZERODHA_SUBMIT_TOKEN: createEndpoint('/auth/zerodha/submit-token'),
    ZERODHA_TEST_CONNECTION: createEndpoint('/auth/zerodha/test-connection'),
    ZERODHA_LOGOUT: createEndpoint('/auth/zerodha/logout'),

    // New endpoints
    ZERODHA_LOGIN: createEndpoint('/api/zerodha/login'),

    // Search endpoints
    SEARCH_SYMBOLS: createEndpoint('/api/v1/search/symbols'),
    SEARCH_TRADES: createEndpoint('/api/v1/search/trades'),
    SEARCH_STRATEGIES: createEndpoint('/api/v1/search/strategies'),
    SEARCH_USERS: createEndpoint('/api/v1/search/users'),
    SEARCH_RECOMMENDATIONS: createEndpoint('/api/v1/search/recommendations'),
    SEARCH_GLOBAL: createEndpoint('/api/v1/search/global'),
    SEARCH_AUTOCOMPLETE: createEndpoint('/api/v1/search/autocomplete'),
};

// Debug logging
// console.log('[API Config] Base URL:', normalizedApiUrl);
// console.log('[API Config] Login URL:', API_ENDPOINTS.LOGIN.url);
// console.log('[API Config] Health URL:', API_ENDPOINTS.HEALTH.url);

// Remove default export as all components use named import
// export default API_ENDPOINTS; 