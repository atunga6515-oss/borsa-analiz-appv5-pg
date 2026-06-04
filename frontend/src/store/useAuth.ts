import { create } from 'zustand';
import api from '../lib/api';

interface AuthState {
  token: string | null;
  username: string | null;
  isAuthenticated: boolean;
  login: (username: string, token: string) => void;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  username: null,
  isAuthenticated: false,
  login: (username, token) => {
    localStorage.setItem('token', token);
    set({ token, username, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, username: null, isAuthenticated: false });
  },
  checkAuth: async () => {
    if (typeof window === 'undefined') return;
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const res = await api.get('/auth/me');
      set({ token, username: res.data.username, isAuthenticated: true });
    } catch {
      localStorage.removeItem('token');
      set({ token: null, username: null, isAuthenticated: false });
    }
  }
}));
