import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@types';
import { authService } from '@services/auth';
import toast from 'react-hot-toast';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (username: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await authService.login(username, password);
          set({ 
            user: response.user, 
            isAuthenticated: true,
            isLoading: false 
          });
          toast.success('Welcome back!');
        } catch (error) {
          set({ isLoading: false });
          toast.error('Invalid credentials');
          throw error;
        }
      },

      logout: async () => {
        try {
          await authService.logout();
          set({ user: null, isAuthenticated: false });
          toast.success('Logged out successfully');
        } catch (error) {
          console.error('Logout error:', error);
        }
      },

      checkAuth: async () => {
        try {
          const response = await authService.checkAuth();
          if (response.id) {
            set({ 
              user: response, 
              isAuthenticated: true 
            });
          }
        } catch (error) {
          set({ user: null, isAuthenticated: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);