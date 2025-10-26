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
    console.log('[WS] Connecting to session:', sessionId);
    console.log('[WS] Handlers being registered:', Object.keys(handlers));

    // Prevent duplicate connections to same session
    if (this.sessionId === sessionId && this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WS] Already connected to session:', sessionId, 'Merging handlers instead of reconnecting');
      // Merge handlers instead of replacing - preserve existing handlers
      this.handlers = { ...this.handlers, ...handlers };
      console.log('[WS] Merged handlers. Now registered:', Object.keys(this.handlers));
      return;
    }

    // If connecting to a different session, close the old connection
    if (this.sessionId !== sessionId && this.ws) {
      console.log('[WS] Closing previous connection to session:', this.sessionId);
      this.ws.close();
    }

    this.sessionId = sessionId;
    // Merge handlers instead of replacing
    this.handlers = { ...this.handlers, ...handlers };

    const wsUrl = getWebSocketUrl(sessionId, WS_URL);
    console.log('[WS] WebSocket URL:', wsUrl);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('[WS] WebSocket opened successfully');
      this.reconnectAttempts = 0;
      this.startPing();
      this.handlers.onConnected?.({
        type: 'connected',
        message: 'Connected to session',
      });
    };

    this.ws.onmessage = (event) => {
      try {
        console.log('[WS] Raw message received:', event.data.substring(0, 100));
        const message: WSIncomingMessage = JSON.parse(event.data);
        console.log('[WS] Message received:', message.type);
        this.handleMessage(message);
      } catch (error) {
        console.error('[WS] Failed to parse message:', error, 'Data:', event.data);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WS] WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('[WS] WebSocket closed');
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
        console.log('[WS] text_chunk handler:', typeof this.handlers.onTextChunk);
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
    const isOpen = this.ws?.readyState === WebSocket.OPEN;
    console.log('[WS] Attempting to send message:', message.type, 'Ready state:', this.ws?.readyState, 'Is open:', isOpen);
    if (isOpen) {
      console.log('[WS] Sending message:', message);
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('[WS] Cannot send message, WebSocket not connected. Ready state:', this.ws?.readyState);
    }
  }

  sendMessage(content: string): void {
    console.log('[WS] sendMessage called with:', content);
    this.send({ type: 'message', content });
  }

  setMode(mode: 'text' | 'audio'): void {
    console.log('[WS] setMode called with:', mode);
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
