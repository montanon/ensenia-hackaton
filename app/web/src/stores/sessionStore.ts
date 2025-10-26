import { create } from 'zustand';
import type { Session, SessionMode, IOMode, CurrentMode } from '../types/session';

interface SessionStore {
  currentSession: Session | null;
  sessionHistory: Session[];
  mode: SessionMode;
  inputMode: IOMode;
  outputMode: IOMode;

  setCurrentSession: (session: Session) => void;
  addToHistory: (session: Session) => void;
  setMode: (mode: SessionMode) => void;
  toggleInputMode: () => void;
  toggleOutputMode: () => void;
  setInputMode: (mode: IOMode) => void;
  setOutputMode: (mode: IOMode) => void;
  getCurrentMode: () => CurrentMode;
  clearSession: () => void;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  currentSession: null,
  sessionHistory: [],
  mode: 'learn',
  inputMode: 'text',
  outputMode: 'text',

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

  clearSession: () => set({ currentSession: null }),
}));
