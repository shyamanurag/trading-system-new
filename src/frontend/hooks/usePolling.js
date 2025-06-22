import { useCallback, useEffect, useRef, useState } from 'react';

const usePolling = (endpoint, interval = 5000) => {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [isPolling, setIsPolling] = useState(false);
    const intervalRef = useRef(null);

    const fetchData = useCallback(async () => {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const jsonData = await response.json();
            setData(jsonData);
            setError(null);
        } catch (err) {
            console.error('Polling error:', err);
            setError(err.message);
        }
    }, [endpoint]);

    const startPolling = useCallback(() => {
        if (isPolling) return;

        setIsPolling(true);
        // Fetch immediately
        fetchData();

        // Then set up interval
        intervalRef.current = setInterval(fetchData, interval);
    }, [fetchData, interval, isPolling]);

    const stopPolling = useCallback(() => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
        setIsPolling(false);
    }, []);

    useEffect(() => {
        startPolling();

        return () => {
            stopPolling();
        };
    }, [startPolling, stopPolling]);

    return {
        data,
        error,
        isPolling,
        refetch: fetchData,
        startPolling,
        stopPolling
    };
};

export default usePolling; 