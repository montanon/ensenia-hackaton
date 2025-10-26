import { create } from 'zustand';

interface AuthStore {
  isAuthenticated: boolean;
  user: { email: string } | null;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  initializeAuth: () => void;
}

const MOCK_EMAIL = 'demo@hackaton.ia';
const MOCK_PASSWORD = 'demo123!';

export const useAuthStore = create<AuthStore>((set) => ({
  isAuthenticated: false,
  user: null,

  login: async (email: string, password: string) => {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 500));

    if (email === MOCK_EMAIL && password === MOCK_PASSWORD) {
      set({ isAuthenticated: true, user: { email } });
      localStorage.setItem('authToken', 'mock-token-' + Date.now());
      localStorage.setItem('userEmail', email);
      return { success: true };
    } else {
      return { success: false, error: 'Invalid email or password' };
    }
  },

  logout: () => {
    set({ isAuthenticated: false, user: null });
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
  },

  initializeAuth: () => {
    const token = localStorage.getItem('authToken');
    const email = localStorage.getItem('userEmail');
    if (token && email) {
      set({ isAuthenticated: true, user: { email } });
    }
  },
}));
