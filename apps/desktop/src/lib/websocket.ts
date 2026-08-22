/**
 * WebSocket connection manager for Jarvis frontend.
 * Handles connection, reconnection, and typed message sending/receiving.
 */

export type JarvisEventType =
  | 'connected'
  | 'pong'
  | 'status_response'
  | 'error'
  | 'state_change'
  | 'transcript'
  | 'ai_response'
  | 'tool_result';

export interface JarvisMessage {
  type: JarvisEventType | string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export type MessageHandler = (message: JarvisMessage) => void;

const WS_URL = 'ws://127.0.0.1:8765/ws';
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

class JarvisWebSocket {
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isIntentionalClose = false;

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    console.log(`[Jarvis WS] Connecting to ${WS_URL}...`);
    this.ws = new WebSocket(WS_URL);

    this.ws.onopen = () => {
      console.log('[Jarvis WS] ✅ Connected!');
      this.reconnectAttempts = 0;
      this.emit('_connected', { connected: true });
    };

    this.ws.onmessage = (event: MessageEvent<string>) => {
      try {
        const message: JarvisMessage = JSON.parse(event.data);
        console.debug('[Jarvis WS] Received:', message.type, message.payload);
        this.emit(message.type, message);
        this.emit('*', message); // wildcard listener
      } catch (err) {
        console.error('[Jarvis WS] Failed to parse message:', event.data, err);
      }
    };

    this.ws.onerror = (event) => {
      console.error('[Jarvis WS] ❌ Error:', event);
      this.emit('_error', { error: 'WebSocket error' });
    };

    this.ws.onclose = (event) => {
      console.warn(`[Jarvis WS] Disconnected (code=${event.code})`);
      this.emit('_disconnected', { connected: false, code: event.code });
      this.ws = null;

      if (!this.isIntentionalClose && this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        this.reconnectAttempts++;
        const delay = RECONNECT_DELAY_MS * Math.min(this.reconnectAttempts, 5);
        console.log(`[Jarvis WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);
        this.reconnectTimer = setTimeout(() => this.connect(), delay);
      }
    };
  }

  disconnect(): void {
    this.isIntentionalClose = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  send(type: string, payload: Record<string, unknown> = {}): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.warn('[Jarvis WS] Cannot send — not connected. Message dropped:', type);
      return;
    }
    const message = JSON.stringify({ type, payload });
    this.ws.send(message);
    console.debug('[Jarvis WS] Sent:', type, payload);
  }

  on(eventType: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(eventType);
      if (handlers) {
        const idx = handlers.indexOf(handler);
        if (idx > -1) handlers.splice(idx, 1);
      }
    };
  }

  private emit(eventType: string, data: unknown): void {
    const handlers = this.handlers.get(eventType) || [];
    handlers.forEach((h) => h(data as JarvisMessage));
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton
export const jarvisWS = new JarvisWebSocket();
