import { defineStore } from 'pinia';
import { apiGet, apiPost, tokens } from '@/services/http';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    ready: false
  }),
  getters: {
    isAuthenticated: (s) => Boolean(s.user),
    // Only sellers (store owners/members) and the super-admin get a dashboard;
    // plain customers do not, so we hide and block the console for them.
    isSeller: (s) => Boolean(s.user?.is_seller || s.user?.is_superuser),
    displayName: (s) => s.user?.first_name || s.user?.email?.split('@')[0] || 'Account'
  },
  actions: {
    async bootstrap() {
      if (tokens.access) {
        try {
          this.user = await apiGet('/auth/me/');
        } catch {
          tokens.clear();
        }
      }
      this.ready = true;
    },
    async login(email, password, remember_me = false) {
      const data = await apiPost('/auth/login/', { email, password, remember_me });
      tokens.set({ access: data.tokens.access, refresh: data.tokens.refresh });
      this.user = data.user;
      return data;
    },
    async register(payload) {
      return apiPost('/auth/register/', payload);
    },
    async loadProfile() {
      this.user = await apiGet('/auth/me/');
    },
    async logout() {
      try {
        await apiPost('/auth/logout/', { refresh: tokens.refresh });
      } catch {
        /* ignore */
      }
      tokens.clear();
      this.user = null;
    }
  }
});
