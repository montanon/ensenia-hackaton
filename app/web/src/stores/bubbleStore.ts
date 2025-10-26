import { create } from 'zustand';

interface BubbleStore {
  isChatOpen: boolean;
  isListening: boolean;

  toggleChat: () => void;
  openChat: () => void;
  closeChat: () => void;
  setListening: (listening: boolean) => void;
}

export const useBubbleStore = create<BubbleStore>((set) => ({
  isChatOpen: false,
  isListening: false,

  toggleChat: () => set((state) => ({ isChatOpen: !state.isChatOpen })),

  openChat: () => set({ isChatOpen: true }),

  closeChat: () => set({ isChatOpen: false }),

  setListening: (listening) => set({ isListening: listening }),
}));
