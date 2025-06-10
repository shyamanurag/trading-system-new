import { useCallback, useEffect, useRef, useState } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export const useWebSocket = (userId = 'default_user') => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);
    const [connectionStats, setConnectionStats] = useState({
        connected: false,
        reconnectAttempts: 0,
        lastError: null
    });

    const ws = useRef(null);
    const reconnectTimeout = useRef(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000; // 3 seconds

    const connect = useCallback(() => {
        try {
            // Close existing connection if any
            if (ws.current?.readyState === WebSocket.OPEN) {
                ws.current.close();
            }

            // Create new WebSocket connection
            const wsUrl = `${WS_BASE_URL}/ws/${userId}`;
            console.log('Connecting to WebSocket:', wsUrl);

            ws.current = new WebSocket(wsUrl);

            ws.current.onopen = () => {
                console.log('WebSocket connected');
                setIsConnected(true);
                reconnectAttempts.current = 0;
                setConnectionStats(prev => ({
                    ...prev,
                    connected: true,
                    reconnectAttempts: 0,
                    lastError: null
                }));

                // Subscribe to market data
                sendMessage({
                    type: 'subscribe',
                    room: 'market_data_NIFTY'
                });
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket message received:', data);
                    setLastMessage(data);

                    // Handle different message types
                    switch (data.type) {
                        case 'CONNECTION_ESTABLISHED':
                            console.log('Connection established:', data.message);
                            break;
                        case 'MARKET_DATA':
                            // Handle market data updates
                            break;
                        case 'TRADE_ALERT':
                            // Handle trade alerts
                            break;
                        case 'SYSTEM_ALERT':
                            // Handle system alerts
                            break;
                        default:
                            console.log('Unknown message type:', data.type);
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            ws.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                setConnectionStats(prev => ({
                    ...prev,
                    lastError: 'Connection error'
                }));
            };

            ws.current.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                setIsConnected(false);
                setConnectionStats(prev => ({
                    ...prev,
                    connected: false
                }));

                // Attempt to reconnect
                if (reconnectAttempts.current < maxReconnectAttempts) {
                    reconnectAttempts.current++;
                    console.log(`Reconnecting... Attempt ${reconnectAttempts.current}/${maxReconnectAttempts}`);

                    reconnectTimeout.current = setTimeout(() => {
                        connect();
                    }, reconnectDelay);
                } else {
                    console.error('Max reconnection attempts reached');
                    setConnectionStats(prev => ({
                        ...prev,
                        lastError: 'Max reconnection attempts reached'
                    }));
                }
            };

        } catch (error) {
            console.error('Error creating WebSocket connection:', error);
            setConnectionStats(prev => ({
                ...prev,
                lastError: error.message
            }));
        }
    }, [userId]);

    const disconnect = useCallback(() => {
        if (reconnectTimeout.current) {
            clearTimeout(reconnectTimeout.current);
        }

        if (ws.current) {
            ws.current.close();
            ws.current = null;
        }

        setIsConnected(false);
        reconnectAttempts.current = 0;
    }, []);

    const sendMessage = useCallback((message) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(message));
            console.log('Message sent:', message);
        } else {
            console.error('WebSocket is not connected');
        }
    }, []);

    const subscribe = useCallback((symbol, provider = 'ALL') => {
        sendMessage({
            type: 'subscribe',
            room: `market_data_${symbol}`
        });
    }, [sendMessage]);

    const unsubscribe = useCallback((symbol, provider = 'ALL') => {
        sendMessage({
            type: 'unsubscribe',
            room: `market_data_${symbol}`
        });
    }, [sendMessage]);

    useEffect(() => {
        connect();

        // Cleanup on unmount
        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    // Send heartbeat every 30 seconds
    useEffect(() => {
        const heartbeatInterval = setInterval(() => {
            if (isConnected) {
                sendMessage({ type: 'heartbeat' });
            }
        }, 30000);

        return () => clearInterval(heartbeatInterval);
    }, [isConnected, sendMessage]);

    return {
        isConnected,
        lastMessage,
        connectionStats,
        sendMessage,
        subscribe,
        unsubscribe,
        reconnect: connect,
        disconnect
    };
}; 