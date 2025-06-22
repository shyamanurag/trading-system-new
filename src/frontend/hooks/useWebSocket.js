import { useCallback, useEffect, useRef, useState } from 'react';

// Use production WebSocket URL from environment variable
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'wss://algoauto-9gx56.ondigitalocean.app/ws';

// Default symbols to subscribe on connection
const DEFAULT_SYMBOLS = ['RELIANCE', 'TCS', 'NIFTY', 'BANKNIFTY', 'INFY', 'HDFCBANK'];

const useWebSocket = (url) => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);
    const [error, setError] = useState(null);
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000; // 3 seconds

    // Use the provided URL or default to WS_BASE_URL
    const wsUrl = url || WS_BASE_URL;

    const connect = useCallback(() => {
        try {
            // Clear any existing connection
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.close();
            }

            console.log(`Connecting to WebSocket: ${wsUrl}`);
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('WebSocket connected');
                setIsConnected(true);
                setError(null);
                reconnectAttemptsRef.current = 0;
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setLastMessage(data);
                } catch (err) {
                    console.error('Error parsing WebSocket message:', err);
                    setLastMessage(event.data);
                }
            };

            ws.onerror = (event) => {
                console.error('WebSocket error:', event);
                setError('WebSocket connection error');
            };

            ws.onclose = (event) => {
                console.log('WebSocket disconnected');
                setIsConnected(false);
                wsRef.current = null;

                // Attempt to reconnect
                if (reconnectAttemptsRef.current < maxReconnectAttempts) {
                    reconnectAttemptsRef.current += 1;
                    console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current}`);

                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, reconnectDelay * reconnectAttemptsRef.current);
                } else {
                    setError('Max reconnection attempts reached');
                }
            };

            wsRef.current = ws;
        } catch (err) {
            console.error('Error creating WebSocket:', err);
            setError(err.message);
        }
    }, [wsUrl]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }

        setIsConnected(false);
        reconnectAttemptsRef.current = 0;
    }, []);

    const sendMessage = useCallback((message) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            const messageStr = typeof message === 'string'
                ? message
                : JSON.stringify(message);
            wsRef.current.send(messageStr);
            return true;
        }
        console.warn('WebSocket is not connected');
        return false;
    }, []);

    // Connect on mount
    useEffect(() => {
        connect();

        // Cleanup on unmount
        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    // Reconnect if URL changes
    useEffect(() => {
        if (wsRef.current) {
            disconnect();
            connect();
        }
    }, [url, connect, disconnect]);

    return {
        isConnected,
        lastMessage,
        error,
        sendMessage,
        reconnect: connect,
        disconnect
    };
};

export default useWebSocket; 