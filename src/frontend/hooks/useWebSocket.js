import { useCallback, useEffect, useRef, useState } from 'react';

// Use production WebSocket URL from environment variable
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'wss://algoauto-ua2iq.ondigitalocean.app';

// Default symbols to subscribe on connection
const DEFAULT_SYMBOLS = ['RELIANCE', 'TCS', 'NIFTY', 'BANKNIFTY', 'INFY', 'HDFCBANK'];

export const useWebSocket = (userId = 'default_user') => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);
    const [connectionStats, setConnectionStats] = useState({
        connected: false,
        reconnectAttempts: 0,
        lastError: null
    });
    const [subscribedSymbols, setSubscribedSymbols] = useState(new Set());

    const ws = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000;
    const mountedRef = useRef(true);

    const sendMessage = useCallback((message) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(message));
            console.log('Sent message:', message);
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }, []);

    const connect = useCallback(() => {
        // Don't connect if already connected or connecting
        if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
            console.log('WebSocket already connected or connecting');
            return;
        }

        // Don't connect if component is unmounted
        if (!mountedRef.current) {
            return;
        }

        try {
            const wsUrl = `${WS_BASE_URL}/ws/${userId}`;
            console.log('Connecting to WebSocket:', wsUrl);

            const newWs = new WebSocket(wsUrl);

            newWs.onopen = () => {
                console.log('WebSocket connected');
                ws.current = newWs;
                setIsConnected(true);
                reconnectAttemptsRef.current = 0;
                setConnectionStats({
                    connected: true,
                    reconnectAttempts: 0,
                    lastError: null
                });

                // Subscribe to default symbols after connection
                setTimeout(() => {
                    DEFAULT_SYMBOLS.forEach(symbol => {
                        sendMessage({
                            type: 'subscribe',
                            room: `market_data_${symbol}`
                        });
                        setSubscribedSymbols(prev => new Set([...prev, symbol]));
                    });
                    console.log(`Subscribed to default symbols: ${DEFAULT_SYMBOLS.join(', ')}`);
                }, 100);
            };

            newWs.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket message received:', data);
                    setLastMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            newWs.onerror = (error) => {
                console.error('WebSocket error:', error);
                setConnectionStats(prev => ({
                    ...prev,
                    lastError: 'Connection error'
                }));
            };

            newWs.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                ws.current = null;
                setIsConnected(false);
                setConnectionStats(prev => ({
                    ...prev,
                    connected: false
                }));

                // Clear subscribed symbols on disconnect
                setSubscribedSymbols(new Set());

                // Attempt to reconnect if component is still mounted
                if (mountedRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
                    reconnectAttemptsRef.current++;
                    console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`);

                    setConnectionStats(prev => ({
                        ...prev,
                        reconnectAttempts: reconnectAttemptsRef.current
                    }));

                    reconnectTimeoutRef.current = setTimeout(() => {
                        if (mountedRef.current) {
                            connect();
                        }
                    }, reconnectDelay);
                }
            };

        } catch (error) {
            console.error('Error creating WebSocket:', error);
            setConnectionStats(prev => ({
                ...prev,
                lastError: error.message
            }));
        }
    }, [userId, sendMessage]);

    const disconnect = useCallback(() => {
        console.log('Disconnecting WebSocket');

        // Clear reconnect timeout
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        // Close WebSocket connection
        if (ws.current) {
            ws.current.close();
            ws.current = null;
        }

        setIsConnected(false);
        setSubscribedSymbols(new Set());
        reconnectAttemptsRef.current = 0;
    }, []);

    const subscribe = useCallback((symbol, provider = 'ALL') => {
        if (!subscribedSymbols.has(symbol)) {
            sendMessage({
                type: 'subscribe',
                room: `market_data_${symbol}`,
                provider: provider
            });
            setSubscribedSymbols(prev => new Set([...prev, symbol]));
            console.log(`Subscribed to ${symbol} (provider: ${provider})`);
        }
    }, [sendMessage, subscribedSymbols]);

    const unsubscribe = useCallback((symbol, provider = 'ALL') => {
        if (subscribedSymbols.has(symbol)) {
            sendMessage({
                type: 'unsubscribe',
                room: `market_data_${symbol}`,
                provider: provider
            });
            setSubscribedSymbols(prev => {
                const newSet = new Set(prev);
                newSet.delete(symbol);
                return newSet;
            });
            console.log(`Unsubscribed from ${symbol} (provider: ${provider})`);
        }
    }, [sendMessage, subscribedSymbols]);

    const subscribeMultiple = useCallback((symbols, provider = 'ALL') => {
        symbols.forEach(symbol => subscribe(symbol, provider));
    }, [subscribe]);

    const unsubscribeAll = useCallback(() => {
        subscribedSymbols.forEach(symbol => unsubscribe(symbol));
    }, [subscribedSymbols, unsubscribe]);

    // Connect on mount
    useEffect(() => {
        mountedRef.current = true;
        connect();

        // Cleanup on unmount
        return () => {
            mountedRef.current = false;
            disconnect();
        };
    }, []); // Empty deps - only run on mount/unmount

    // Heartbeat
    useEffect(() => {
        const heartbeatInterval = setInterval(() => {
            if (isConnected && ws.current?.readyState === WebSocket.OPEN) {
                sendMessage({ type: 'heartbeat' });
            }
        }, 30000);

        return () => clearInterval(heartbeatInterval);
    }, [isConnected, sendMessage]);

    return {
        isConnected,
        lastMessage,
        connectionStats,
        subscribedSymbols: Array.from(subscribedSymbols),
        sendMessage,
        subscribe,
        unsubscribe,
        subscribeMultiple,
        unsubscribeAll,
        reconnect: connect,
        disconnect
    };
}; 