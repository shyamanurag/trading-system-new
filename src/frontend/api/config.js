// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://algoauto-jd32t.ondigitalocean.app';

export const API_ENDPOINTS = {
    // Auth endpoints
    LOGIN: `${API_BASE_URL}/api/v1/auth/login`,
    REGISTER: `${API_BASE_URL}/api/v1/auth/register`,
    LOGOUT: `${API_BASE_URL}/api/v1/auth/logout`,
    REFRESH_TOKEN: `${API_BASE_URL}/api/v1/auth/refresh-token`,
    // ... existing code ...
}; 