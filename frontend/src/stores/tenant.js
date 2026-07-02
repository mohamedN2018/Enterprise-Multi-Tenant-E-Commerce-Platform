import { defineStore } from 'pinia';
import { activeStore, apiGet } from '@/services/http';

// The admin's member stores + the currently-selected one (X-Store-Id).
export const useTenantStore = defineStore('tenant', {
  state: () => ({
    stores: [],
    activeId: activeStore.id,
    loading: false
  }),
  getters: {
    active: (s) => s.stores.find((x) => x.id === s.activeId) || null,
    hasStores: (s) => s.stores.length > 0,
    currency: (s) => s.stores.find((x) => x.id === s.activeId)?.currency || 'USD'
  },
  actions: {
    async refresh() {
      this.loading = true;
      try {
        const data = await apiGet('/stores/');
        this.stores = Array.isArray(data) ? data : data?.results || [];
        const stillValid = this.stores.some((s) => s.id === this.activeId);
        if (this.stores.length && !stillValid) {
          this.select(this.stores[0].id);
        }
      } finally {
        this.loading = false;
      }
    },
    // Guarantee a valid active store before store-scoped calls. Returns the id
    // (or null if the user owns no stores yet).
    async ensureReady() {
      if (!this.stores.length) await this.refresh();
      return this.activeId || null;
    },
    select(id) {
      activeStore.set(id);
      this.activeId = id;
    }
  }
});
