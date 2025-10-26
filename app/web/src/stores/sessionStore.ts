import { create } from 'zustand';
import type { Session, SessionMode, IOMode, CurrentMode } from '../types/session';

interface InitStatus {
  research_loaded: boolean;
  initial_exercises_ready: boolean;
  exercise_count: number;
  learning_content_ready?: boolean;
  study_guide_ready?: boolean;
  pending_exercises?: number;
  pool_health?: string;
}

interface SessionStore {
  currentSession: Session | null;
  sessionHistory: Session[];
  mode: SessionMode;
  inputMode: IOMode;
  outputMode: IOMode;
  isInitializing: boolean;
  initStatus: InitStatus;
  initError: string | null;

  setCurrentSession: (session: Session) => void;
  addToHistory: (session: Session) => void;
  setMode: (mode: SessionMode) => void;
  toggleInputMode: () => void;
  toggleOutputMode: () => void;
  setInputMode: (mode: IOMode) => void;
  setOutputMode: (mode: IOMode) => void;
  getCurrentMode: () => CurrentMode;
  clearSession: () => void;
  setInitializing: (isInitializing: boolean) => void;
  setInitStatus: (status: InitStatus) => void;
  setInitError: (error: string | null) => void;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  currentSession: null,
  sessionHistory: [],
  mode: 'learn',
  inputMode: 'text',
  outputMode: 'text',
  isInitializing: false,
  initStatus: {
    research_loaded: false,
    initial_exercises_ready: false,
    exercise_count: 0,
  },
  initError: null,

  setCurrentSession: (session) => set({ currentSession: session }),

  addToHistory: (session) => set((state) => ({
    sessionHistory: [session, ...state.sessionHistory.filter(s => s.id !== session.id)]
  })),

  setMode: (mode) => set({ mode }),

  toggleInputMode: () => set((state) => ({
    inputMode: state.inputMode === 'text' ? 'voice' : 'text'
  })),

  toggleOutputMode: () => set((state) => ({
    outputMode: state.outputMode === 'text' ? 'voice' : 'text'
  })),

  setInputMode: (mode) => set({ inputMode: mode }),

  setOutputMode: (mode) => set({ outputMode: mode }),

  getCurrentMode: () => {
    const { outputMode } = get();
    return outputMode === 'voice' ? 'audio' : 'text';
  },

  clearSession: () => set({
    currentSession: null,
    isInitializing: false,
    initStatus: {
      research_loaded: false,
      initial_exercises_ready: false,
      exercise_count: 0,
      learning_content_ready: false,
      study_guide_ready: false,
      pending_exercises: 0,
    },
    initError: null,
  }),

  setInitializing: (isInitializing) => set({ isInitializing }),

  setInitStatus: (status) => set({ initStatus: status }),

  setInitError: (error) => set({ initError: error }),
}));
