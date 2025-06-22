// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://algoauto-9gx56.ondigitalocean.app';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'wss://algoauto-9gx56.ondigitalocean.app';

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

    // User endpoints - These use /api/v1/users prefix - FIXED: Added trailing slash
    USERS: createEndpoint('/api/v1/users/', true),
    USER_PROFILE: createEndpoint('/api/v1/users/profile'),
    USER_PERFORMANCE: createEndpoint('/api/v1/users/performance'),
    USER_CURRENT: createEndpoint('/api/v1/users/current'),

    // Broker user management
    BROKER_USERS: createEndpoint('/api/v1/control/users/broker'),

    // Trading endpoints - FIXED: Added /api prefix
    TRADES: createEndpoint('/api/v1/trades'),
    POSITIONS: createEndpoint('/api/v1/positions'),
    ORDERS: createEndpoint('/api/v1/orders'),

    // Trading control endpoints
    TRADING_CONTROL: createEndpoint('/api/v1/control/trading/control'),
    TRADING_STATUS: createEndpoint('/api/v1/control/trading/status'),

    // Market data endpoints - These use /api/market prefix
    MARKET_INDICES: createEndpoint('/api/market/indices'),
    MARKET_STATUS: createEndpoint('/api/market/market-status'),
    MARKET_DATA: createEndpoint('/api/market/data'),
    SYMBOLS: createEndpoint('/api/market/symbols'),

    // Strategy endpoints - FIXED: Added /api prefix
    STRATEGIES: createEndpoint('/api/v1/strategies'),
    STRATEGY_PERFORMANCE: createEndpoint('/api/v1/strategies/performance'),

    // Dashboard endpoints - FIXED: Added /api prefix
    DASHBOARD_SUMMARY: createEndpoint('/api/v1/dashboard/dashboard/summary'),
    DAILY_PNL: createEndpoint('/api/v1/monitoring/daily-pnl'),
    RECOMMENDATIONS: createEndpoint('/api/v1/recommendations'),

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
    AUTONOMOUS_CONTROL: createEndpoint('/api/v1/autonomous/control'),

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
    CONFIG: createEndpoint('/config')
};

// Debug logging
console.log('[API Config] Base URL:', normalizedApiUrl);
console.log('[API Config] Login URL:', API_ENDPOINTS.LOGIN.url);
console.log('[API Config] Health URL:', API_ENDPOINTS.HEALTH.url);

export default API_ENDPOINTS; 