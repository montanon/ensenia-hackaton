export type MessageRole = 'user' | 'assistant';

export interface Message {
  id?: number;
  session_id?: number;
  role: MessageRole;
  content: string;
  timestamp?: string;
  audio_id?: string;
  audio_url?: string;
  audio_available?: boolean;
  audio_duration?: number;
}

export interface SendMessageRequest {
  message: string;
}
