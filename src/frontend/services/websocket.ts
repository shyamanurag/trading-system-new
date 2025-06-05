import { EventEmitter } from 'events';

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
}

class WebSocketService extends EventTarget {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private url: string;

  constructor(url: string = 'ws://localhost:8000/ws') {
    super();
    this.url = url;
  }

  connect(callbacks?: WebSocketCallbacks): void {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        callbacks?.onConnect?.();
        this.dispatchEvent(new Event('connect'));
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        callbacks?.onDisconnect?.();
        this.dispatchEvent(new Event('disconnect'));
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        callbacks?.onError?.(error);
        this.dispatchEvent(new Event('error'));
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          callbacks?.onMessage?.(message);
          this.dispatchEvent(new CustomEvent('message', { detail: message }));
          this.dispatchEvent(new CustomEvent(`message:${message.type}`, { detail: message }));
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      this.handleReconnect();
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  subscribe(event: string, callback: (data: any) => void): void {
    this.addEventListener(event, ((e: CustomEvent) => callback(e.detail)) as EventListener);
  }

  unsubscribe(event: string, callback: (data: any) => void): void {
    this.removeEventListener(event, ((e: CustomEvent) => callback(e.detail)) as EventListener);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();

// Export hook for React components
export const useWebSocket = () => {
  return websocketService;
}; 