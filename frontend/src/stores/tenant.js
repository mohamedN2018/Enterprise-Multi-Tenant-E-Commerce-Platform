import { defineStore } from 'pinia';
import { activeStore, apiGet } from '@/services/http';
import { t } from '@/i18n';
import { useAuthStore } from './auth';

// Roles that may write store data / manage members, mirroring the backend:
//   write (catalog, inventory, orders, promotions, settings) → manager|owner
//   team management (change role / remove) & store deletion   → owner only
const WRITE_ROLES = ['owner', 'manager', 'platform'];
const OWNER_ROLES = ['owner', 'platform'];

// The admin's member stores, the selected one (X-Store-Id), and the caller's
// role within it (drives permission-gated UI).
export const useTenantStore = defineStore('tenant', {
  state: () => ({
    stores: [],
    activeId: activeStore.id,
    loading: false,
    role: null,
    roleForStore: null
  }),
  getters: {
    active: (s) => s.stores.find((x) => x.id === s.activeId) || null,
    hasStores: (s) => s.stores.length > 0,
    currency: (s) => s.stores.find((x) => x.id === s.activeId)?.currency || 'USD',
    isPlatform: (s) => s.role === 'platform',
    canWrite: (s) => WRITE_ROLES.includes(s.role),
    canManageMembers: (s) => WRITE_ROLES.includes(s.role), // view + add
    canAdminTeam: (s) => OWNER_ROLES.includes(s.role), // change role / remove
    canDeleteStore: (s) => OWNER_ROLES.includes(s.role),
    roleLabel: (s) => (s.role ? t(`roles.${s.role}`) : t('roles.member'))
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
    // Determine the caller's role for the active store. Superusers are platform
    // admins ("owner of all stores"); otherwise owner via store.owner, else the
    // membership role (managers/owners can list members; employees get 403).
    async resolveRole() {
      const auth = useAuthStore();
      if (auth.user?.is_superuser) {
        this.role = 'platform';
        this.roleForStore = this.activeId;
        return this.role;
      }
      const store = this.active;
      if (!store) {
        this.role = null;
        return null;
      }
      if (this.roleForStore === store.id && this.role) return this.role;
      if (store.owner && store.owner === auth.user?.id) {
        this.role = 'owner';
      } else {
        try {
          const members = await apiGet(`/stores/${store.id}/members/`);
          const list = Array.isArray(members) ? members : members?.results || [];
          const mine = list.find((m) => m.user_email === auth.user?.email);
          this.role = mine?.role || 'manager';
        } catch {
          this.role = 'employee';
        }
      }
      this.roleForStore = store.id;
      return this.role;
    },
    // Guarantee a valid active store + resolved role before store-scoped calls.
    async ensureReady() {
      if (!this.stores.length) await this.refresh();
      if (this.activeId && this.roleForStore !== this.activeId) await this.resolveRole();
      return this.activeId || null;
    },
    select(id) {
      activeStore.set(id);
      this.activeId = id;
      this.role = null;
      this.roleForStore = null;
    }
  }
});
