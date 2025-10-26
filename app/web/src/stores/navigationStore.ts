import { create } from 'zustand';

export type PageType = 'learn' | 'practice' | 'review' | 'evaluacion';

interface NavigationStore {
  currentPage: PageType;
  setCurrentPage: (page: PageType) => void;
}

export const useNavigationStore = create<NavigationStore>((set) => ({
  currentPage: 'learn',
  setCurrentPage: (page) => set({ currentPage: page }),
}));
