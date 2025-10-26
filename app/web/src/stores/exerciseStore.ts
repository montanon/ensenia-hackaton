import { create } from 'zustand';
import type { Exercise } from '../types/exercise';
import { exerciseApi } from '../services/api';

interface ExerciseStore {
  currentExercise: Exercise | null;
  exerciseSessionId: number | null;
  isGenerating: boolean;

  // Exercise pool
  exercisePool: Exercise[];
  poolSize: number;
  isLoadingPool: boolean;

  setCurrentExercise: (exercise: Exercise, sessionId?: number) => void;
  clearExercise: () => void;
  setGenerating: (generating: boolean) => void;

  // Pool management
  loadExercisePool: (sessionId: number) => Promise<void>;
  getNextExercise: () => Exercise | null;
  clearPool: () => void;
}

export const useExerciseStore = create<ExerciseStore>((set, get) => ({
  currentExercise: null,
  exerciseSessionId: null,
  isGenerating: false,

  exercisePool: [],
  poolSize: 0,
  isLoadingPool: false,

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

  loadExercisePool: async (sessionId: number) => {
    set({ isLoadingPool: true });
    try {
      const exercises = await exerciseApi.getSessionExercises(sessionId);
      set({
        exercisePool: exercises,
        poolSize: exercises.length,
        isLoadingPool: false,
      });
    } catch (error) {
      console.error('[ExerciseStore] Failed to load exercise pool:', error);
      set({ isLoadingPool: false });
    }
  },

  getNextExercise: () => {
    const { exercisePool } = get();
    if (exercisePool.length === 0) return null;

    // Return first exercise from pool
    const nextExercise = exercisePool[0];

    // Remove from pool
    set(state => ({
      exercisePool: state.exercisePool.slice(1),
      poolSize: state.poolSize - 1,
    }));

    return nextExercise;
  },

  clearPool: () => set({
    exercisePool: [],
    poolSize: 0,
  }),
}));
