// Enhanced utility with caching, retry logic, and rate limiting

// Simple in-memory cache
const cache = new Map();
const requestHistory = new Map();

// Cache TTL configuration (milliseconds)
const CACHE_TTL = {
    dashboard: 30000,      // 30 seconds
    elite: 60000,          // 1 minute
    market: 5000,          // 5 seconds
    positions: 15000,      // 15 seconds
    default: 60000         // 1 minute default
};

// Rate limiting configuration
const RATE_LIMITS = {
    '/api/v1/autonomous/': { max: 10, window: 60000 },
    '/api/market/': { max: 60, window: 60000 },
    '/api/v1/elite/': { max: 30, window: 60000 },
    default: { max: 20, window: 60000 }
};

// Get cache TTL for URL
function getCacheTTL(url) {
    for (const [key, ttl] of Object.entries(CACHE_TTL)) {
        if (url.includes(key)) return ttl;
    }
    return CACHE_TTL.default;
}

// Get rate limit for URL
function getRateLimit(url) {
    for (const [pattern, limit] of Object.entries(RATE_LIMITS)) {
        if (url.includes(pattern)) return limit;
    }
    return RATE_LIMITS.default;
}

// Check rate limit
function checkRateLimit(url) {
    const limit = getRateLimit(url);
    const now = Date.now();
    
    if (!requestHistory.has(url)) {
        requestHistory.set(url, []);
    }
    
    const history = requestHistory.get(url);
    const cutoff = now - limit.window;
    const recent = history.filter(time => time > cutoff);
    
    if (recent.length >= limit.max) {
        const oldestRequest = Math.min(...recent);
        const waitTime = oldestRequest + limit.window - now;
        console.warn(`[RateLimit] Exceeded for ${url}, wait ${Math.ceil(waitTime/1000)}s`);
        return { allowed: false, waitTime };
    }
    
    recent.push(now);
    requestHistory.set(url, recent);
    return { allowed: true };
}

// Cache management
function getFromCache(url) {
    const cached = cache.get(url);
    if (!cached) return null;
    
    const age = Date.now() - cached.timestamp;
    const ttl = getCacheTTL(url);
    
    if (age > ttl) {
        cache.delete(url);
        return null;
    }
    
    console.log(`[Cache] HIT: ${url} (age: ${Math.round(age/1000)}s)`);
    return cached.data;
}

function setCache(url, data) {
    cache.set(url, { data, timestamp: Date.now() });
}

// Retry with exponential backoff
async function fetchWithRetry(url, options, maxRetries = 3) {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const response = await fetch(url, options);
            
            if (response.ok) {
                if (attempt > 0) console.log(`[Retry] SUCCESS on attempt ${attempt + 1}`);
                return response;
            }
            
            // Don't retry client errors (except 429 rate limit)
            if (response.status >= 400 && response.status < 500 && response.status !== 429) {
                return response;
            }
            
            // Retry server errors with exponential backoff
            if (attempt < maxRetries - 1) {
                const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
                console.warn(`[Retry] Attempt ${attempt + 1} failed, retrying in ${delay}ms`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        } catch (error) {
            if (attempt === maxRetries - 1) throw error;
            const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
            console.warn(`[Retry] Network error, retrying in ${delay}ms`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
}

// Main authenticated fetch with all enhancements
export const fetchWithAuth = async (url, options = {}) => {
    const token = localStorage.getItem('access_token');
    
    // Check rate limit
    const rateCheck = checkRateLimit(url);
    if (!rateCheck.allowed) {
        const error = new Error(`Rate limit exceeded. Retry after ${Math.ceil(rateCheck.waitTime/1000)}s`);
        error.rateLimited = true;
        throw error;
    }
    
    // Check cache for GET requests
    if (!options.method || options.method === 'GET') {
        const cached = getFromCache(url);
        if (cached) {
            return {
                ok: true,
                status: 200,
                json: async () => cached,
                fromCache: true
            };
        }
    }

    const headers = {
        'Accept': 'application/json',
        ...options.headers
    };

    if (options.body) {
        headers['Content-Type'] = 'application/json';
    }

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetchWithRetry(url, { ...options, headers }, 3);

        // Handle 401 Unauthorized
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_info');
            window.location.reload();
            throw new Error('Authentication required');
        }

        // Cache successful GET responses
        if (response.ok && (!options.method || options.method === 'GET')) {
            try {
                const cloned = response.clone();
                const data = await cloned.json();
                setCache(url, data);
            } catch (e) {
                // Ignore cache errors
            }
        }

        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
};

// Clear cache utility
export const clearCache = (pattern) => {
    if (pattern) {
        for (const [key] of cache.entries()) {
            if (key.includes(pattern)) cache.delete(key);
        }
    } else {
        cache.clear();
    }
};

// Network detection
export const isOnline = () => navigator.onLine;

export default fetchWithAuth; 