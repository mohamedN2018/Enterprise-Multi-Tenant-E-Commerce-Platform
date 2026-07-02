<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  LayoutDashboard,
  Activity,
  Package,
  Tags,
  Bookmark,
  SlidersHorizontal,
  ShoppingBag,
  Boxes,
  BadgePercent,
  Megaphone,
  Gift,
  Truck,
  Undo2,
  CreditCard,
  Wallet,
  Landmark,
  Layers,
  Building2,
  ShieldAlert,
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
import { t } from '@/i18n';

const router = useRouter();
const auth = useAuthStore();
const tenant = useTenantStore();

const sidebarOpen = ref(false);
const storeMenu = ref(false);

// Grouped, role-aware navigation.
const navGroups = computed(() => [
  {
    title: t('admin.overview'),
    links: [
      { label: t('admin.dashboard'), to: { name: 'admin-dashboard' }, icon: LayoutDashboard },
      { label: t('admin.analytics'), to: { name: 'admin-analytics' }, icon: Activity },
      ...(tenant.isPlatform ? [{ label: t('admin.platform'), to: { name: 'admin-platform' }, icon: Globe }] : [])
    ]
  },
  {
    title: t('admin.catalog'),
    links: [
      { label: t('admin.products'), to: { name: 'admin-products' }, icon: Package },
      { label: t('admin.categories'), to: { name: 'admin-categories' }, icon: Tags },
      { label: t('admin.brands'), to: { name: 'admin-brands' }, icon: Bookmark },
      { label: t('admin.attributes'), to: { name: 'admin-attributes' }, icon: SlidersHorizontal }
    ]
  },
  {
    title: t('admin.sales'),
    links: [
      { label: t('admin.orders'), to: { name: 'admin-orders' }, icon: ShoppingBag },
      { label: t('admin.returns'), to: { name: 'admin-returns' }, icon: Undo2 },
      { label: t('admin.payments'), to: { name: 'admin-payments' }, icon: CreditCard },
      { label: t('admin.reviews'), to: { name: 'admin-reviews' }, icon: Star }
    ]
  },
  {
    title: t('admin.marketing'),
    links: [
      { label: t('admin.promotions'), to: { name: 'admin-promotions' }, icon: BadgePercent },
      { label: t('admin.campaigns'), to: { name: 'admin-campaigns' }, icon: Megaphone },
      { label: t('admin.giftCards'), to: { name: 'admin-giftcards' }, icon: Gift }
    ]
  },
  {
    title: t('admin.operations'),
    links: [
      { label: t('admin.inventory'), to: { name: 'admin-inventory' }, icon: Boxes },
      { label: t('admin.shipping'), to: { name: 'admin-shipping' }, icon: Truck },
      { label: t('admin.procurement'), to: { name: 'admin-procurement' }, icon: Building2 },
      { label: t('admin.pricing'), to: { name: 'admin-pricing' }, icon: Layers },
      { label: t('admin.fraud'), to: { name: 'admin-fraud' }, icon: ShieldAlert }
    ]
  },
  {
    title: t('admin.finance'),
    links: [
      { label: t('admin.payouts'), to: { name: 'admin-payouts' }, icon: Wallet },
      { label: t('admin.finance'), to: { name: 'admin-finance' }, icon: Landmark }
    ]
  },
  {
    title: t('admin.store'),
    links: [
      { label: t('admin.notifications'), to: { name: 'admin-notifications' }, icon: Bell },
      ...(tenant.canManageMembers ? [{ label: t('admin.team'), to: { name: 'admin-team' }, icon: Users }] : []),
      { label: t('admin.settings'), to: { name: 'admin-settings' }, icon: Settings }
    ]
  }
]);

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
      class="fixed inset-y-0 start-0 z-40 flex w-64 flex-col border-e border-slate-200 bg-white transition-transform lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full rtl:translate-x-full'"
    >
      <div class="flex h-16 items-center gap-2 border-b border-slate-100 px-4">
        <img src="/brand/qtech-logo.png" alt="q-shop" class="h-9 w-auto" />
        <span class="font-heading text-sm font-bold text-slate-500">{{ tenant.isPlatform ? $t('admin.admin') : $t('admin.seller') }}</span>
      </div>

      <div class="border-b border-slate-100 p-3">
        <div class="relative">
          <button
            class="flex w-full items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-start hover:bg-slate-50"
            @click="storeMenu = !storeMenu"
          >
            <span class="grid h-8 w-8 place-items-center rounded-md bg-primary-100 text-xs font-bold text-primary-700">
              {{ (activeStore?.name || '?').charAt(0).toUpperCase() }}
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-semibold">{{ activeStore?.name || $t('admin.selectStore') }}</span>
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
            <p v-if="!tenant.stores.length" class="px-4 py-2 text-sm text-slate-400">{{ $t('admin.noStores') }}</p>
          </div>
        </div>
        <div v-if="tenant.role" class="mt-2 px-1">
          <span class="chip border-0" :class="roleTone[tenant.role] || 'bg-slate-100 text-slate-600'">
            <ShieldCheck class="h-3 w-3" /> {{ tenant.roleLabel }}
          </span>
        </div>
      </div>

      <nav class="flex-1 space-y-4 overflow-y-auto p-3">
        <div v-for="group in navGroups" :key="group.title">
          <p class="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">{{ group.title }}</p>
          <div class="space-y-0.5">
            <RouterLink
              v-for="link in group.links"
              :key="link.label"
              :to="link.to"
              class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-ink"
              active-class="bg-primary-50 text-primary-700"
            >
              <component :is="link.icon" class="h-5 w-5" />
              {{ link.label }}
            </RouterLink>
          </div>
        </div>
      </nav>

      <div class="border-t border-slate-100 p-3">
        <RouterLink :to="{ name: 'home' }" class="dropdown-item rounded-lg">
          <ExternalLink class="h-4 w-4" /> {{ $t('admin.viewStorefront') }}
        </RouterLink>
        <button class="dropdown-item w-full rounded-lg text-rose-600" @click="logout">
          <LogOut class="h-4 w-4" /> {{ $t('account.signOut') }}
        </button>
      </div>
    </aside>

    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
      @click="sidebarOpen = false"
    ></div>

    <!-- Main -->
    <div class="lg:ps-64">
      <header class="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur lg:px-8">
        <button
          class="grid h-10 w-10 place-items-center rounded-lg hover:bg-slate-100 lg:hidden"
          @click="sidebarOpen = true"
        >
          <Menu class="h-5 w-5" />
        </button>
        <div class="ms-auto flex items-center gap-3">
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
