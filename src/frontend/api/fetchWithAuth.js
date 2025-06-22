// Utility function for authenticated fetch requests
export const fetchWithAuth = async (url, options = {}) => {
    const token = localStorage.getItem('access_token');

    const headers = {
        'Accept': 'application/json',
        ...options.headers
    };

    // Only add Content-Type for requests with body
    if (options.body) {
        headers['Content-Type'] = 'application/json';
    }

    // Add authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        // Handle 401 Unauthorized
        if (response.status === 401) {
            // Clear auth data and redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_info');
            window.location.reload();
            throw new Error('Authentication required');
        }

        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
};

export default fetchWithAuth; 