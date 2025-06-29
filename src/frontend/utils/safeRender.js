/**
 * Safe Rendering Utilities for React Components
 * Prevents React Error #31 (Objects are not valid as a React child)
 */

/**
 * Safely renders any value for display in React components
 * @param {any} value - The value to render
 * @param {string} fallback - Fallback text if value cannot be rendered
 * @returns {string} A safely renderable string
 */
export const safeRender = (value, fallback = 'N/A') => {
    if (value === null || value === undefined) {
        return fallback;
    }

    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
        return String(value);
    }

    if (typeof value === 'object') {
        // Handle arrays
        if (Array.isArray(value)) {
            return value.length > 0 ? value.join(', ') : fallback;
        }

        // Handle objects - convert to readable format
        try {
            // Handle TrueData deployment status object (React Error #31 fix)
            if (value.hasOwnProperty('deployment_id') && value.hasOwnProperty('connection_attempts')) {
                return `TrueData: ${value.connected ? 'Connected' : 'Disconnected'} | Deployment: ${value.deployment_id?.substring(0, 8) || 'Unknown'}`;
            }

            // For common status objects, extract key information
            if (value.hasOwnProperty('connected') && value.hasOwnProperty('symbols_active')) {
                // TrueData status object
                return `TrueData: ${value.connected ? 'Connected' : 'Disconnected'} | Symbols: ${value.symbols_active || 0}`;
            }

            if (value.hasOwnProperty('status') && value.hasOwnProperty('message')) {
                // Generic status object
                return `${value.status}: ${value.message}`;
            }

            // Generic object - show key properties
            const keys = Object.keys(value).slice(0, 3); // Show first 3 keys
            const preview = keys.map(key => `${key}: ${safeRender(value[key])}`).join(', ');
            return preview || fallback;

        } catch (error) {
            console.warn('safeRender: Error processing object:', error);
            return fallback;
        }
    }

    return String(value);
};

/**
 * Safely renders a status object with formatted output
 * @param {object} statusObj - Status object (e.g., TrueData status)
 * @param {string} type - Type hint for better formatting
 * @returns {string} Formatted status string
 */
export const safeRenderStatus = (statusObj, type = 'generic') => {
    if (!statusObj || typeof statusObj !== 'object') {
        return 'Status: Unknown';
    }

    try {
        switch (type) {
            case 'truedata':
                // Handle TrueData deployment status object (prevents React Error #31)
                if (statusObj.hasOwnProperty('deployment_id') && statusObj.hasOwnProperty('connection_attempts')) {
                    return `TrueData: ${statusObj.connected ? 'Connected' : 'Disconnected'} | Deploy: ${statusObj.deployment_id?.substring(0, 8) || 'Unknown'} | Attempts: ${statusObj.connection_attempts || 0}`;
                }
                return `TrueData: ${statusObj.connected ? 'Connected' : 'Disconnected'} | Symbols: ${statusObj.symbols_active || 0}`;

            case 'zerodha':
                return `Zerodha: ${statusObj.authenticated ? 'Authenticated' : 'Not Authenticated'}`;

            case 'market':
                return `Market: ${statusObj.market_open ? 'Open' : 'Closed'}`;

            default:
                return safeRender(statusObj);
        }
    } catch (error) {
        console.warn('safeRenderStatus: Error processing status object:', error);
        return 'Status: Error';
    }
};

/**
 * Safely extracts and renders a specific property from an object
 * @param {object} obj - The object to extract from
 * @param {string} path - Dot notation path (e.g., 'status.connected')
 * @param {any} fallback - Fallback value
 * @returns {string} Safely rendered property value
 */
export const safeGet = (obj, path, fallback = 'N/A') => {
    try {
        const value = path.split('.').reduce((current, key) => current?.[key], obj);
        return safeRender(value, fallback);
    } catch (error) {
        console.warn('safeGet: Error accessing path:', path, error);
        return fallback;
    }
};

export default safeRender; 