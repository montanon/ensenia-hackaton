import type { CurrentMode, SessionMode } from './session';

export type WSMessageType =
  | 'connected'
  | 'text_chunk'
  | 'audio_ready'
  | 'stt_partial'
  | 'stt_result'
  | 'mode_changed'
  | 'message_complete'
  | 'error'
  | 'pong';

export interface WSConnectedMessage {
  type: 'connected';
  session_id: number;
  current_mode: CurrentMode;
  grade: number;
  subject: string;
  mode: SessionMode;
}

export interface WSTextChunkMessage {
  type: 'text_chunk';
  content: string;
}

export interface WSAudioReadyMessage {
  type: 'audio_ready';
  audio_id: string;
  url: string;
  duration?: number;
}

export interface WSSTTPartialMessage {
  type: 'stt_partial';
  transcript: string;
  confidence?: number;
}

export interface WSSTTResultMessage {
  type: 'stt_result';
  transcript: string;
  confidence?: number;
}

export interface WSModeChangedMessage {
  type: 'mode_changed';
  mode: CurrentMode;
}

export interface WSMessageCompleteMessage {
  type: 'message_complete';
  message_id?: number;
}

export interface WSErrorMessage {
  type: 'error';
  message: string;
  code?: string;
}

export interface WSPongMessage {
  type: 'pong';
}

export type WSIncomingMessage =
  | WSConnectedMessage
  | WSTextChunkMessage
  | WSAudioReadyMessage
  | WSSTTPartialMessage
  | WSSTTResultMessage
  | WSModeChangedMessage
  | WSMessageCompleteMessage
  | WSErrorMessage
  | WSPongMessage;

export interface WSSendMessagePayload {
  type: 'message';
  content: string;
}

export interface WSSetModePayload {
  type: 'set_mode';
  mode: CurrentMode;
}

export interface WSPingPayload {
  type: 'ping';
}

export interface WSAudioChunkPayload {
  type: 'audio_chunk';
  data: string; // base64 encoded audio
}

export interface WSAudioEndPayload {
  type: 'audio_end';
}

export type WSOutgoingMessage =
  | WSSendMessagePayload
  | WSSetModePayload
  | WSPingPayload
  | WSAudioChunkPayload
  | WSAudioEndPayload;
