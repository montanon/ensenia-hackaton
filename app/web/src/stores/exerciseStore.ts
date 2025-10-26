import { create } from 'zustand';
import type { Exercise } from '../types/exercise';

interface ExerciseStore {
  currentExercise: Exercise | null;
  exerciseSessionId: number | null;
  isGenerating: boolean;

  setCurrentExercise: (exercise: Exercise, sessionId?: number) => void;
  clearExercise: () => void;
  setGenerating: (generating: boolean) => void;
}

export const useExerciseStore = create<ExerciseStore>((set) => ({
  currentExercise: null,
  exerciseSessionId: null,
  isGenerating: false,

  setCurrentExercise: (exercise, sessionId) => set({
    currentExercise: exercise,
    exerciseSessionId: sessionId ?? null,
    isGenerating: false,
  }),

  clearExercise: () => set({
    currentExercise: null,
    exerciseSessionId: null,
  }),

  setGenerating: (generating) => set({ isGenerating: generating }),
}));
