export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface WebSocketCallbacks {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onBatchMessage?: (messages: WebSocketMessage[]) => void;
}

interface WebSocketConfig {
  url: string;
  reconnectAttempts: number;
  reconnectDelay: number;
  heartbeatInterval: number;
  batchSize: number;
  batchInterval: number;
}

class WebSocketService extends EventTarget {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval = 30000;
  private batchSize = 50;
  private batchInterval = 100;
  private messageQueue: WebSocketMessage[] = [];
  private batchTimer: ReturnType<typeof setInterval> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private url: string;
  private isConnecting = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isOnline = true;
  private networkHandlers: { online: () => void; offline: () => void } | null = null;

  constructor(config?: Partial<WebSocketConfig>) {
    super();
    // Use environment variable with fallback to relative path
    const wsUrl = import.meta.env.VITE_WS_URL;
    if (!wsUrl) {
      console.warn('VITE_WS_URL not set, using relative WebSocket URL');
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      this.url = `${protocol}//${window.location.host}/ws`;
    } else {
      this.url = wsUrl;
    }
    this.maxReconnectAttempts = config?.reconnectAttempts || 5;
    this.reconnectDelay = config?.reconnectDelay || 1000;
    this.heartbeatInterval = config?.heartbeatInterval || 30000;
    this.batchSize = config?.batchSize || 50;
    this.batchInterval = config?.batchInterval || 100;
    
    // Setup network detection
    this.setupNetworkDetection();
  }
  
  private setupNetworkDetection(): void {
    this.isOnline = navigator.onLine;
    
    const handleOnline = () => {
      console.log('[Network] Back online, attempting to reconnect WebSocket');
      this.isOnline = true;
      this.dispatchEvent(new Event('network_online'));
      if (!this.isConnected() && !this.isConnecting) {
        this.reconnectAttempts = 0; // Reset attempts on network recovery
        this.connect();
      }
    };
    
    const handleOffline = () => {
      console.warn('[Network] Offline detected, pausing WebSocket');
      this.isOnline = false;
      this.dispatchEvent(new Event('network_offline'));
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    this.networkHandlers = { online: handleOnline, offline: handleOffline };
  }
  
  private cleanupNetworkDetection(): void {
    if (this.networkHandlers) {
      window.removeEventListener('online', this.networkHandlers.online);
      window.removeEventListener('offline', this.networkHandlers.offline);
      this.networkHandlers = null;
    }
  }
  
  getNetworkStatus(): boolean {
    return this.isOnline;
  }

  connect(callbacks?: WebSocketCallbacks): void {
    if (this.isConnecting) return;
    this.isConnecting = true;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.startBatchTimer();
        callbacks?.onConnect?.();
        this.dispatchEvent(new Event('connect'));
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnecting = false;
        this.stopHeartbeat();
        this.stopBatchTimer();
        callbacks?.onDisconnect?.();
        this.dispatchEvent(new Event('disconnect'));

        // Only attempt reconnect if not closed cleanly
        if (event.code !== 1000) {
          this.handleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        callbacks?.onError?.(error);
        this.dispatchEvent(new Event('error'));
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          // Handle batch messages
          if (message.type === 'batch' && Array.isArray(message.messages)) {
            callbacks?.onBatchMessage?.(message.messages);
            message.messages.forEach(msg => {
              this.dispatchEvent(new CustomEvent(`message:${msg.type}`, { detail: msg }));
            });
          } else {
            callbacks?.onMessage?.(message);
            this.dispatchEvent(new CustomEvent('message', { detail: message }));
            this.dispatchEvent(new CustomEvent(`message:${message.type}`, { detail: message }));
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      this.isConnecting = false;
      this.handleReconnect();
    }
  }

  private handleReconnect(): void {
    // Don't reconnect if offline
    if (!this.isOnline) {
      console.log('[Network] Offline, skipping reconnect attempt');
      return;
    }
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

      // Clear any existing reconnect timer
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
      }

      // Calculate exponential backoff delay
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 30000);

      this.reconnectTimer = setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      this.dispatchEvent(new Event('reconnect_failed'));
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'heartbeat', data: null, timestamp: new Date().toISOString() });
      }
    }, this.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private startBatchTimer(): void {
    this.stopBatchTimer();
    this.batchTimer = setInterval(() => {
      this.flushMessageQueue();
    }, this.batchInterval);
  }

  private stopBatchTimer(): void {
    if (this.batchTimer) {
      clearInterval(this.batchTimer);
      this.batchTimer = null;
    }
  }

  private flushMessageQueue(): void {
    if (this.messageQueue.length > 0 && this.isConnected()) {
      const messages = this.messageQueue.splice(0, this.batchSize);
      this.ws?.send(JSON.stringify({
        type: 'batch',
        messages,
        timestamp: new Date().toISOString()
      }));
    }
  }

  disconnect(): void {
    this.stopHeartbeat();
    this.stopBatchTimer();
    this.flushMessageQueue();
    this.cleanupNetworkDetection();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: WebSocketMessage): void {
    if (!this.isConnected()) {
      console.error('WebSocket is not connected');
      return;
    }

    // Add to message queue for batching
    this.messageQueue.push(message);

    // Send immediately if queue is full
    if (this.messageQueue.length >= this.batchSize) {
      this.flushMessageQueue();
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }

  getMessageQueueSize(): number {
    return this.messageQueue.length;
  }

  // New method to subscribe to topics
  subscribe(topics: string[]): void {
      if (!this.isConnected()) {
          console.error('Cannot subscribe: WebSocket not connected');
          return;
      }
      this.send({
          type: 'subscribe',
          topics: topics,
          timestamp: new Date().toISOString()
      });
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();

// Export hook for React components
export const useWebSocket = () => {
  return websocketService;
};