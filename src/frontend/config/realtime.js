// Real-time data configuration
// Determines whether to use WebSocket or Polling based on deployment environment

const isDigitalOcean = window.location.hostname.includes('ondigitalocean.app');
const isDevelopment = import.meta.env.DEV;

export const REALTIME_CONFIG = {
    // Use polling on Digital Ocean due to Cloudflare proxy limitations
    // Use WebSocket in development or other deployments
    strategy: isDigitalOcean ? 'polling' : 'websocket',

    // Polling intervals (in milliseconds)
    polling: {
        marketData: 3000,      // 3 seconds for market data
        positions: 5000,       // 5 seconds for positions
        orders: 5000,          // 5 seconds for orders
        systemStatus: 10000,   // 10 seconds for system status
        alerts: 15000          // 15 seconds for alerts
    },

    // WebSocket configuration
    websocket: {
        url: import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`,
        reconnectInterval: 5000,
        heartbeatInterval: 30000
    },

    // Feature flags
    features: {
        showConnectionStatus: true,
        autoReconnect: true,
        showLatency: isDevelopment
    }
};

// Helper function to get appropriate component based on strategy
export const useRealtimeStrategy = () => {
    return REALTIME_CONFIG.strategy;
};

export default REALTIME_CONFIG; 