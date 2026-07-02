<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  LayoutDashboard,
  Package,
  Tags,
  Bookmark,
  ShoppingBag,
  Boxes,
  BadgePercent,
  Truck,
  Undo2,
  Wallet,
  Users,
  Settings,
  Store as StoreIcon,
  ChevronDown,
  Menu,
  X,
  ExternalLink,
  LogOut,
  ShieldCheck,
  Globe,
  Star,
  Bell
} from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useTenantStore } from '@/stores/tenant';
import NotificationBell from '@/components/ui/NotificationBell.vue';

const router = useRouter();
const auth = useAuthStore();
const tenant = useTenantStore();

const sidebarOpen = ref(false);
const storeMenu = ref(false);

const baseLinks = [
  { label: 'Dashboard', to: { name: 'admin-dashboard' }, icon: LayoutDashboard },
  { label: 'Products', to: { name: 'admin-products' }, icon: Package },
  { label: 'Categories', to: { name: 'admin-categories' }, icon: Tags },
  { label: 'Brands', to: { name: 'admin-brands' }, icon: Bookmark },
  { label: 'Orders', to: { name: 'admin-orders' }, icon: ShoppingBag },
  { label: 'Inventory', to: { name: 'admin-inventory' }, icon: Boxes },
  { label: 'Shipping', to: { name: 'admin-shipping' }, icon: Truck },
  { label: 'Returns', to: { name: 'admin-returns' }, icon: Undo2 },
  { label: 'Promotions', to: { name: 'admin-promotions' }, icon: BadgePercent },
  { label: 'Reviews', to: { name: 'admin-reviews' }, icon: Star },
  { label: 'Payouts', to: { name: 'admin-payouts' }, icon: Wallet },
  { label: 'Notifications', to: { name: 'admin-notifications' }, icon: Bell },
  { label: 'Team', to: { name: 'admin-team' }, icon: Users, requires: 'members' },
  { label: 'Settings', to: { name: 'admin-settings' }, icon: Settings }
];

// Nav is role-aware: employees don't see Team (they can't list members);
// platform admins get a Platform overview link at the top.
const links = computed(() => {
  const items = baseLinks.filter((l) => l.requires !== 'members' || tenant.canManageMembers);
  if (tenant.isPlatform) {
    return [{ label: 'Platform', to: { name: 'admin-platform' }, icon: Globe }, ...items];
  }
  return items;
});

const roleTone = {
  platform: 'bg-secondary-100 text-secondary-700',
  owner: 'bg-primary-100 text-primary-700',
  manager: 'bg-sky-100 text-sky-700',
  employee: 'bg-slate-100 text-slate-600'
};

const activeStore = computed(() => tenant.active);

const pickStore = (id) => {
  tenant.select(id);
  storeMenu.value = false;
  router.go(0);
};

const logout = async () => {
  await auth.logout();
  router.push({ name: 'login' });
};

onMounted(() => tenant.ensureReady());
watch(() => router.currentRoute.value.fullPath, () => (sidebarOpen.value = false));
</script>

<template>
  <div class="min-h-screen bg-slate-100 text-ink">
    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="flex h-16 items-center gap-2 border-b border-slate-100 px-5 font-heading font-bold">
        <span class="grid h-9 w-9 place-items-center rounded-lg bg-primary-600 text-white">
          <StoreIcon class="h-5 w-5" />
        </span>
        {{ tenant.isPlatform ? 'Admin Center' : 'Seller Center' }}
      </div>

      <div class="border-b border-slate-100 p-3">
        <div class="relative">
          <button
            class="flex w-full items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-left hover:bg-slate-50"
            @click="storeMenu = !storeMenu"
          >
            <span class="grid h-8 w-8 place-items-center rounded-md bg-primary-100 text-xs font-bold text-primary-700">
              {{ (activeStore?.name || '?').charAt(0).toUpperCase() }}
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-semibold">{{ activeStore?.name || 'Select store' }}</span>
              <span class="block truncate text-xs text-slate-400">{{ activeStore?.slug || '—' }}</span>
            </span>
            <ChevronDown class="h-4 w-4 text-slate-400" />
          </button>
          <div
            v-if="storeMenu"
            class="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-pop"
          >
            <button
              v-for="s in tenant.stores"
              :key="s.id"
              class="dropdown-item w-full"
              :class="s.id === tenant.activeId ? 'bg-primary-50 text-primary-700' : ''"
              @click="pickStore(s.id)"
            >
              {{ s.name }}
            </button>
            <p v-if="!tenant.stores.length" class="px-4 py-2 text-sm text-slate-400">No stores yet</p>
          </div>
        </div>
        <div v-if="tenant.role" class="mt-2 px-1">
          <span class="chip border-0" :class="roleTone[tenant.role] || 'bg-slate-100 text-slate-600'">
            <ShieldCheck class="h-3 w-3" /> {{ tenant.roleLabel }}
          </span>
        </div>
      </div>

      <nav class="flex-1 space-y-1 overflow-y-auto p-3">
        <RouterLink
          v-for="link in links"
          :key="link.label"
          :to="link.to"
          class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-ink"
          active-class="bg-primary-50 text-primary-700"
        >
          <component :is="link.icon" class="h-5 w-5" />
          {{ link.label }}
        </RouterLink>
      </nav>

      <div class="border-t border-slate-100 p-3">
        <RouterLink :to="{ name: 'home' }" class="dropdown-item rounded-lg">
          <ExternalLink class="h-4 w-4" /> View storefront
        </RouterLink>
        <button class="dropdown-item w-full rounded-lg text-rose-600" @click="logout">
          <LogOut class="h-4 w-4" /> Sign out
        </button>
      </div>
    </aside>

    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
      @click="sidebarOpen = false"
    ></div>

    <!-- Main -->
    <div class="lg:pl-64">
      <header class="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur lg:px-8">
        <button
          class="grid h-10 w-10 place-items-center rounded-lg hover:bg-slate-100 lg:hidden"
          @click="sidebarOpen = true"
        >
          <Menu class="h-5 w-5" />
        </button>
        <div class="ml-auto flex items-center gap-3">
          <NotificationBell />
          <span class="hidden text-sm text-slate-500 sm:inline">{{ auth.user?.email }}</span>
          <span class="grid h-9 w-9 place-items-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700">
            {{ auth.displayName.charAt(0).toUpperCase() }}
          </span>
        </div>
      </header>

      <main class="p-4 lg:p-8">
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>
