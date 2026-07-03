import { defineStore } from 'pinia';
import http from '@/services/http';
import { useAuthStore } from './auth';

const SHOP_KEY = 'shop_store';
const loadShop = () => {
  try {
    return JSON.parse(localStorage.getItem(SHOP_KEY) || 'null');
  } catch {
    return null;
  }
};

// Storefront cart: server-side cart scoped to the shopped store (checkout is
// per-store). The store is sent explicitly as X-Store-Id on every cart call.
export const useCartStore = defineStore('cart', {
  state: () => ({ shopStore: loadShop(), cart: null, loading: false, drawerOpen: false }),
  getters: {
    count: (s) => s.cart?.item_count || 0,
    headers: (s) => (s.shopStore ? { 'X-Store-Id': s.shopStore.id } : {})
  },
  actions: {
    openDrawer() {
      this.drawerOpen = true;
    },
    closeDrawer() {
      this.drawerOpen = false;
    },
    setShopStore(store) {
      const slim = store
        ? { id: store.id, slug: store.slug, name: store.name, currency: store.currency }
        : null;
      if (slim) localStorage.setItem(SHOP_KEY, JSON.stringify(slim));
      else localStorage.removeItem(SHOP_KEY);
      this.shopStore = slim;
    },
    async refreshCart() {
      const auth = useAuthStore();
      if (!auth.isAuthenticated || !this.shopStore) {
        this.cart = null;
        return;
      }
      this.loading = true;
      try {
        const r = await http.get('/cart/', { headers: this.headers });
        this.cart = r.data;
      } catch {
        this.cart = null;
      } finally {
        this.loading = false;
      }
    },
    async addItem(variantId, quantity = 1) {
      await http.post('/cart/items/', { variant_id: variantId, quantity }, { headers: this.headers });
      await this.refreshCart();
    },
    async updateItem(itemId, quantity) {
      await http.patch(`/cart/items/${itemId}/`, { quantity }, { headers: this.headers });
      await this.refreshCart();
    },
    async removeItem(itemId) {
      await http.delete(`/cart/items/${itemId}/`, { headers: this.headers });
      await this.refreshCart();
    },
    async applyCoupon(code) {
      await http.post('/cart/coupon/', { code }, { headers: this.headers });
      await this.refreshCart();
    },
    async removeCoupon() {
      await http.delete('/cart/coupon/', { headers: this.headers });
      await this.refreshCart();
    },
    async checkout(options = {}) {
      const r = await http.post('/cart/checkout/', options, { headers: this.headers });
      await this.refreshCart();
      return r.data;
    }
  }
});
