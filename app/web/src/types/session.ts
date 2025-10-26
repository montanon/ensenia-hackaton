export type SessionMode = 'learn' | 'practice' | 'study' | 'evaluation';
export type IOMode = 'text' | 'voice';
export type CurrentMode = 'text' | 'audio';

export interface Session {
  id: number;
  created_at: string;
  grade: number;
  subject: string;
  mode: SessionMode;
  research_context?: string;
  current_mode: CurrentMode;
}

export interface CreateSessionRequest {
  grade: number;
  subject: string;
  mode: SessionMode;
  topic?: string;
}

export interface CreateSessionResponse {
  session_id: number;
  grade: number;
  subject: string;
  mode: SessionMode;
  context_loaded: boolean;
  created_at: string;
}
