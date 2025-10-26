import { WS_URL } from '../utils/constants';
import { getWebSocketUrl } from '../utils/helpers';
import type {
  WSIncomingMessage,
  WSOutgoingMessage,
  WSConnectedMessage,
  WSTextChunkMessage,
  WSAudioReadyMessage,
  WSModeChangedMessage,
  WSMessageCompleteMessage,
  WSErrorMessage,
} from '../types/websocket';

type MessageHandler = {
  onConnected?: (msg: WSConnectedMessage) => void;
  onTextChunk?: (msg: WSTextChunkMessage) => void;
  onAudioReady?: (msg: WSAudioReadyMessage) => void;
  onModeChanged?: (msg: WSModeChangedMessage) => void;
  onMessageComplete?: (msg: WSMessageCompleteMessage) => void;
  onError?: (msg: WSErrorMessage) => void;
  onDisconnect?: () => void;
};

export class WebSocketService {
  private ws: WebSocket | null = null;
  private sessionId: number | null = null;
  private handlers: MessageHandler = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pingInterval: number | null = null;

  connect(sessionId: number, handlers: MessageHandler): void {
    this.sessionId = sessionId;
    this.handlers = handlers;

    const wsUrl = getWebSocketUrl(sessionId, WS_URL);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('[WS] Connected to session:', sessionId);
      this.reconnectAttempts = 0;
      this.startPing();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WSIncomingMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('[WS] Failed to parse message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WS] WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('[WS] Disconnected');
      this.stopPing();
      this.handlers.onDisconnect?.();
      this.attemptReconnect();
    };
  }

  private handleMessage(message: WSIncomingMessage): void {
    switch (message.type) {
      case 'connected':
        this.handlers.onConnected?.(message);
        break;
      case 'text_chunk':
        this.handlers.onTextChunk?.(message);
        break;
      case 'audio_ready':
        this.handlers.onAudioReady?.(message);
        break;
      case 'mode_changed':
        this.handlers.onModeChanged?.(message);
        break;
      case 'message_complete':
        this.handlers.onMessageComplete?.(message);
        break;
      case 'error':
        this.handlers.onError?.(message);
        break;
      case 'pong':
        // Ping response received
        break;
      default:
        console.warn('[WS] Unknown message type:', message);
    }
  }

  send(message: WSOutgoingMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('[WS] Cannot send message, WebSocket not connected');
    }
  }

  sendMessage(content: string): void {
    this.send({ type: 'message', content });
  }

  setMode(mode: 'text' | 'audio'): void {
    this.send({ type: 'set_mode', mode });
  }

  private startPing(): void {
    this.pingInterval = window.setInterval(() => {
      this.send({ type: 'ping' });
    }, 30000); // Ping every 30 seconds
  }

  private stopPing(): void {
    if (this.pingInterval !== null) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WS] Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      if (this.sessionId) {
        this.connect(this.sessionId, this.handlers);
      }
    }, delay);
  }

  disconnect(): void {
    this.stopPing();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
    this.reconnectAttempts = 0;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const websocketService = new WebSocketService();
