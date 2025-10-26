import { create } from 'zustand';

export type PageType = 'landing' | 'login' | 'learn' | 'practice' | 'review' | 'study' | 'evaluacion';

interface NavigationStore {
  currentPage: PageType;
  setCurrentPage: (page: PageType) => void;
}

export const useNavigationStore = create<NavigationStore>((set) => ({
  currentPage: 'landing',
  setCurrentPage: (page) => set({ currentPage: page }),
}));
