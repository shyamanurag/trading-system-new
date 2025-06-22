// Utility function for authenticated fetch requests
export const fetchWithAuth = async (url, options = {}) => {
    const token = localStorage.getItem('access_token');

    const headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...options.headers
    };

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