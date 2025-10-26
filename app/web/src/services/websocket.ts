import { WS_URL } from '../utils/constants';
import { getWebSocketUrl } from '../utils/helpers';
import type {
  WSIncomingMessage,
  WSOutgoingMessage,
  WSConnectedMessage,
  WSTextChunkMessage,
  WSAudioReadyMessage,
  WSSTTPartialMessage,
  WSSTTResultMessage,
  WSModeChangedMessage,
  WSMessageCompleteMessage,
  WSErrorMessage,
} from '../types/websocket';

// WebSocket configuration constants
const MAX_RECONNECT_ATTEMPTS = 5;
const INITIAL_RECONNECT_DELAY_MS = 1000;
const PING_INTERVAL_MS = 30000;

export type MessageHandler = {
  onConnected?: (msg: WSConnectedMessage) => void;
  onTextChunk?: (msg: WSTextChunkMessage) => void;
  onAudioReady?: (msg: WSAudioReadyMessage) => void;
  onSTTPartial?: (msg: WSSTTPartialMessage) => void;
  onSTTResult?: (msg: WSSTTResultMessage) => void;
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
  private maxReconnectAttempts = MAX_RECONNECT_ATTEMPTS;
  private reconnectDelay = INITIAL_RECONNECT_DELAY_MS;
  private pingInterval: number | null = null;
  private additionalHandlers: MessageHandler = {};

  connect(sessionId: number, handlers: MessageHandler): void {
    this.sessionId = sessionId;
    this.handlers = handlers;

    const wsUrl = getWebSocketUrl(sessionId, WS_URL);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
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
      this.stopPing();
      this.handlers.onDisconnect?.();
      this.attemptReconnect();
    };
  }

  private handleMessage(message: WSIncomingMessage): void {
    switch (message.type) {
      case 'connected':
        this.handlers.onConnected?.(message);
        this.additionalHandlers.onConnected?.(message);
        break;
      case 'text_chunk':
        this.handlers.onTextChunk?.(message);
        this.additionalHandlers.onTextChunk?.(message);
        break;
      case 'audio_ready':
        this.handlers.onAudioReady?.(message);
        this.additionalHandlers.onAudioReady?.(message);
        break;
      case 'stt_partial':
        this.handlers.onSTTPartial?.(message);
        this.additionalHandlers.onSTTPartial?.(message);
        break;
      case 'stt_result':
        this.handlers.onSTTResult?.(message);
        this.additionalHandlers.onSTTResult?.(message);
        break;
      case 'mode_changed':
        this.handlers.onModeChanged?.(message);
        this.additionalHandlers.onModeChanged?.(message);
        break;
      case 'message_complete':
        this.handlers.onMessageComplete?.(message);
        this.additionalHandlers.onMessageComplete?.(message);
        break;
      case 'error':
        this.handlers.onError?.(message);
        this.additionalHandlers.onError?.(message);
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

  sendAudioChunk(audioData: string): void {
    this.send({ type: 'audio_chunk', data: audioData });
  }

  sendAudioEnd(): void {
    this.send({ type: 'audio_end' });
  }

  /**
   * Register additional message handlers (for components like VoiceButton)
   * Allows multiple listeners for the same message types
   */
  registerAdditionalHandlers(handlers: MessageHandler): void {
    this.additionalHandlers = handlers;
  }

  /**
   * Unregister additional message handlers
   */
  unregisterAdditionalHandlers(): void {
    this.additionalHandlers = {};
  }

  private startPing(): void {
    this.pingInterval = window.setInterval(() => {
      this.send({ type: 'ping' });
    }, PING_INTERVAL_MS);
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
