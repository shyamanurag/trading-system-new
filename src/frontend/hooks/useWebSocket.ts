import { useEffect, useCallback, useState } from 'react';
import { websocketService, WebSocketMessage, WebSocketCallbacks } from '../services/websocket';

export const useWebSocket = (callbacks?: WebSocketCallbacks) => {
  const [isConnected, setIsConnected] = useState(false);
  const [networkStatus, setNetworkStatus] = useState(true);

  useEffect(() => {
    // Enhanced callbacks with connection state tracking
    const enhancedCallbacks: WebSocketCallbacks = {
      ...callbacks,
      onConnect: () => {
        setIsConnected(true);
        callbacks?.onConnect?.();
      },
      onDisconnect: () => {
        setIsConnected(false);
        callbacks?.onDisconnect?.();
      }
    };

    // Setup WebSocket connection
    websocketService.connect(enhancedCallbacks);
    
    // Setup network status monitoring
    const handleNetworkOnline = () => setNetworkStatus(true);
    const handleNetworkOffline = () => setNetworkStatus(false);
    
    websocketService.addEventListener('network_online', handleNetworkOnline);
    websocketService.addEventListener('network_offline', handleNetworkOffline);
    
    // Initial state
    setIsConnected(websocketService.isConnected());
    setNetworkStatus(websocketService.getNetworkStatus());

    return () => {
      websocketService.removeEventListener('network_online', handleNetworkOnline);
      websocketService.removeEventListener('network_offline', handleNetworkOffline);
      websocketService.disconnect();
    };
  }, [callbacks]);

  const send = useCallback((message: WebSocketMessage) => {
    websocketService.send(message);
  }, []);

  const subscribe = useCallback((event: string, callback: (data: any) => void) => {
    websocketService.subscribe(event, callback);
    return () => websocketService.unsubscribe(event, callback);
  }, []);

  return {
    send,
    subscribe,
    isConnected,
    networkStatus,
    reconnectAttempts: websocketService.getReconnectAttempts(),
    queueSize: websocketService.getMessageQueueSize()
  };
}; 