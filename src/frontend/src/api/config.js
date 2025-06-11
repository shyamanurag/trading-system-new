// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://algoauto-ua2iq.ondigitalocean.app/api';

export const API_ENDPOINTS = {
    // Auth endpoints
    LOGIN: `${API_BASE_URL}/auth/login`,
    REGISTER: `${API_BASE_URL}/auth/register`,
    LOGOUT: `${API_BASE_URL}/auth/logout`,
    REFRESH_TOKEN: `${API_BASE_URL}/auth/refresh-token`,

    // User endpoints
    USERS: `${API_BASE_URL}/users`,
    USER_PROFILE: `${API_BASE_URL}/users/profile`,

    // Trading endpoints
    TRADES: `${API_BASE_URL}/trades`,
    POSITIONS: `${API_BASE_URL}/positions`,
    ORDERS: `${API_BASE_URL}/orders`,

    // Market data endpoints
    MARKET_DATA: `${API_BASE_URL}/market-data`,
    SYMBOLS: `${API_BASE_URL}/symbols`,

    // Strategy endpoints
    STRATEGIES: `${API_BASE_URL}/strategies`,
    STRATEGY_PERFORMANCE: `${API_BASE_URL}/strategies/performance`,

    // Broker endpoints
    BROKER_CONNECT: `${API_BASE_URL}/broker/connect`,
    BROKER_DISCONNECT: `${API_BASE_URL}/broker/disconnect`,
    BROKER_STATUS: `${API_BASE_URL}/broker/status`,

    // System endpoints
    SYSTEM_STATUS: `${API_BASE_URL}/system/status`,
    SYSTEM_LOGS: `${API_BASE_URL}/system/logs`,
    SYSTEM_METRICS: `${API_BASE_URL}/system/metrics`
};

export default API_ENDPOINTS; 