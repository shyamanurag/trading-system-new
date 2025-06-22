import { useCallback, useEffect, useRef, useState } from 'react';
import fetchWithAuth from '../api/fetchWithAuth';

/**
 * Custom hook for polling API endpoints
 * @param {string} url - The API endpoint to poll
 * @param {number} interval - Polling interval in milliseconds
 * @param {boolean} enabled - Whether polling is enabled
 */
export const usePolling = (url, interval = 5000, enabled = true) => {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const intervalRef = useRef(null);

    const fetchData = useCallback(async () => {
        if (!url || !enabled) return;

        try {
            const response = await fetchWithAuth(url);
            if (response.ok) {
                const result = await response.json();
                setData(result);
                setError(null);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (err) {
            setError(err.message);
            // Don't clear data on error - keep showing last successful data
        } finally {
            setLoading(false);
        }
    }, [url, enabled]);

    useEffect(() => {
        if (!enabled) {
            setLoading(false);
            return;
        }

        // Initial fetch
        fetchData();

        // Set up polling
        intervalRef.current = setInterval(fetchData, interval);

        // Cleanup
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [fetchData, interval, enabled]);

    return { data, error, loading, refetch: fetchData };
};

export default usePolling; 