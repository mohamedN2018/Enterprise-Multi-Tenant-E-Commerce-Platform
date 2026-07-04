import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

// The admin/seller consoles share the same pages under two URL prefixes
// (/admin/* and /seller/*). `cr(key)` builds a route for the CURRENT console,
// falling back to the caller's role when we're outside a console (storefront).
export function useConsole() {
  const route = useRoute();
  const auth = useAuthStore();
  const base = computed(() => {
    const p = route.path || '';
    if (p.startsWith('/seller')) return 'seller';
    if (p.startsWith('/admin')) return 'admin';
    return auth.user?.is_superuser ? 'admin' : 'seller';
  });
  const cr = (key, params) => ({ name: `${base.value}-${key}`, ...(params ? { params } : {}) });
  return { base, cr };
}
