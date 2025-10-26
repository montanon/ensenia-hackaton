import axios from 'axios';
import { API_URL } from '../utils/constants';
import type {
  CreateSessionRequest,
  CreateSessionResponse,
  Session,
} from '../types/session';
import type {
  GenerateExerciseRequest,
  Exercise,
  SubmitAnswerRequest,
  GenerateExerciseResponse,
  LinkExerciseResponse,
  SubmitAnswerResponse,
} from '../types/exercise';
import type { SendMessageRequest, SendMessageResponse } from '../types/message';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Session API
export const sessionApi = {
  create: async (data: CreateSessionRequest): Promise<CreateSessionResponse> => {
    const response = await api.post<CreateSessionResponse>('/chat/sessions', data);
    return response.data;
  },

  get: async (sessionId: number): Promise<Session> => {
    const response = await api.get<Session>(`/chat/sessions/${sessionId}`);
    return response.data;
  },

  sendMessage: async (sessionId: number, data: SendMessageRequest): Promise<SendMessageResponse> => {
    const response = await api.post<SendMessageResponse>(`/chat/sessions/${sessionId}/messages`, data);
    return response.data;
  },

  triggerResearch: async (sessionId: number, topic: string): Promise<void> => {
    await api.post(`/chat/sessions/${sessionId}/research`, { topic });
  },

  updateMode: async (sessionId: number, mode: string): Promise<void> => {
    await api.patch(`/chat/sessions/${sessionId}/mode`, { mode });
  },

  getStatus: async (sessionId: number): Promise<{
    session_id: number;
    research_loaded: boolean;
    initial_exercises_ready: boolean;
    exercise_count: number;
    pending_exercises: number;
    pool_health: string;
    learning_content_ready: boolean;
    study_guide_ready: boolean;
  }> => {
    const response = await api.get(`/chat/sessions/${sessionId}/status`);
    return response.data;
  },

  getLearningContent: async (sessionId: number): Promise<any> => {
    const response = await api.get(`/chat/sessions/${sessionId}/learning-content`);
    return response.data;
  },

  getStudyGuide: async (sessionId: number): Promise<any> => {
    const response = await api.get(`/chat/sessions/${sessionId}/study-guide`);
    return response.data;
  },
};

// Exercise API
export const exerciseApi = {
  generate: async (data: GenerateExerciseRequest): Promise<GenerateExerciseResponse> => {
    const response = await api.post<GenerateExerciseResponse>('/exercises/generate', data);
    return response.data;
  },

  get: async (exerciseId: number): Promise<Exercise> => {
    const response = await api.get<Exercise>(`/exercises/${exerciseId}`);
    return response.data;
  },

  assignToSession: async (exerciseId: number, sessionId: number): Promise<LinkExerciseResponse> => {
    const response = await api.post<LinkExerciseResponse>(`/exercises/${exerciseId}/sessions/${sessionId}`);
    return response.data;
  },

  submit: async (exerciseSessionId: number, data: SubmitAnswerRequest): Promise<SubmitAnswerResponse> => {
    const response = await api.post<SubmitAnswerResponse>(`/exercises/sessions/${exerciseSessionId}/submit`, data);
    return response.data;
  },

  getSessionExercises: async (sessionId: number): Promise<Exercise[]> => {
    const response = await api.get<{ exercises: Array<{ exercise: Exercise; exercise_session_id: number }>; total: number }>(`/exercises/sessions/${sessionId}/exercises`);
    // Map the response to include exercise_session_id in the exercise object
    return response.data.exercises.map(item => ({
      ...item.exercise,
      exercise_session_id: item.exercise_session_id,
    }));
  },
};

// TTS API
export const ttsApi = {
  speak: (text: string, grade: number): string => {
    return `${API_URL}/tts/speak?text=${encodeURIComponent(text)}&grade=${grade}`;
  },

  stream: (text: string, grade: number): string => {
    return `${API_URL}/tts/stream?text=${encodeURIComponent(text)}&grade=${grade}`;
  },
};

// Health checks
export const healthApi = {
  check: async (): Promise<any> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
