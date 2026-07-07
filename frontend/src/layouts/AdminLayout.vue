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
  Bell,
  Volume2,
  VolumeX,
  Plus,
  Send,
  ArrowLeft,
  LogIn
} from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import NotificationBell from '@/components/ui/NotificationBell.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';
import { useValidation, required, positive, iso2 } from '@/utils/validators';
import { t } from '@/i18n';
import { useTheme } from '@/theme';
import { useConsole } from '@/composables/useConsole';
import { useOrderAlerts, orderSoundMuted, toggleOrderSound } from '@/composables/useOrderAlerts';

// Ping the seller (sound + toast) the moment a new order lands.
useOrderAlerts();

const ui = useUiStore();

// Seller store allotment: create up to max_stores, then request more.
const maxStores = computed(() => Number(auth.user?.max_stores) || 1);
const canCreateStore = computed(() => !tenant.isPlatform && tenant.stores.length < maxStores.value);
const atStoreLimit = computed(() => !tenant.isPlatform && tenant.stores.length >= maxStores.value);

const showCreateStore = ref(false);
const creatingStore = ref(false);
const storeForm = ref({ name: '', country: '' });
const { errors: csErr, run: runCs, clear: clearCs } = useValidation(() => storeForm.value, {
  name: [required()],
  country: [iso2({ optional: true })]
});
const openCreateStore = () => {
  storeForm.value = { name: '', country: '' };
  storeMenu.value = false;
  showCreateStore.value = true;
};
const createStore = async () => {
  if (!runCs()) return;
  creatingStore.value = true;
  try {
    const res = await seller.createStore({ name: storeForm.value.name, country: storeForm.value.country });
    ui.success(t('storeSwitcher.storeCreated'));
    showCreateStore.value = false;
    await tenant.refresh();
    if (res.data?.id) {
      tenant.select(res.data.id);
      router.go(0);
    }
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    creatingStore.value = false;
  }
};

const showStoreReq = ref(false);
const storeReqBusy = ref(false);
const storeReqForm = ref({ requested_limit: 2, note: '' });
const { errors: srErr, run: runSr, clear: clearSr } = useValidation(() => storeReqForm.value, {
  requested_limit: [positive()]
});
const openStoreReq = () => {
  storeReqForm.value = { requested_limit: maxStores.value + 1, note: '' };
  storeMenu.value = false;
  showStoreReq.value = true;
};
const requestStores = async () => {
  if (!runSr()) return;
  storeReqBusy.value = true;
  try {
    await seller.requestStores({
      requested_limit: Number(storeReqForm.value.requested_limit),
      note: storeReqForm.value.note
    });
    ui.success(t('storeSwitcher.requestSent'));
    showStoreReq.value = false;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    storeReqBusy.value = false;
  }
};

const { theme } = useTheme();

const router = useRouter();
const auth = useAuthStore();
const tenant = useTenantStore();
const { cr } = useConsole();

const sidebarOpen = ref(false);
const storeMenu = ref(false);

// The admin has two modes: the platform panel (managing stores/sellers) and,
// once they enter a store, full store management. Sellers are always in-store.
const isAdmin = computed(() => tenant.isAdmin);
const inStore = computed(() => tenant.viewingStore);

// Platform-panel navigation (admin, not inside a store).
const platformGroups = computed(() => [
  {
    title: t('admin.platformTitle'),
    links: [{ label: t('admin.adminPanel'), to: cr('platform'), icon: Globe }]
  }
]);

// Store-management navigation — sellers always, admin once inside a store.
// Each link carries its permission `area`; employees only see areas they were
// granted (owners/managers/platform see everything — canArea returns true).
const storeGroups = computed(() => [
  {
    title: t('admin.overview'),
    links: [
      { label: t('admin.dashboard'), to: cr('dashboard'), icon: LayoutDashboard },
      { label: t('admin.analytics'), to: cr('analytics'), icon: Activity }
    ]
  },
  {
    title: t('admin.catalog'),
    links: [
      { label: t('admin.products'), to: cr('products'), icon: Package, area: 'catalog' },
      { label: t('admin.categories'), to: cr('categories'), icon: Tags, area: 'catalog' },
      { label: t('admin.brands'), to: cr('brands'), icon: Bookmark, area: 'catalog' },
      { label: t('admin.attributes'), to: cr('attributes'), icon: SlidersHorizontal, area: 'catalog' }
    ]
  },
  {
    title: t('admin.sales'),
    links: [
      { label: t('admin.orders'), to: cr('orders'), icon: ShoppingBag, area: 'sales' },
      { label: t('admin.returns'), to: cr('returns'), icon: Undo2, area: 'sales' },
      { label: t('admin.payments'), to: cr('payments'), icon: CreditCard, area: 'sales' },
      { label: t('admin.reviews'), to: cr('reviews'), icon: Star, area: 'sales' }
    ]
  },
  {
    title: t('admin.marketing'),
    links: [
      { label: t('admin.promotions'), to: cr('promotions'), icon: BadgePercent, area: 'marketing' },
      { label: t('admin.campaigns'), to: cr('campaigns'), icon: Megaphone, area: 'marketing' },
      { label: t('admin.giftCards'), to: cr('giftcards'), icon: Gift, area: 'marketing' }
    ]
  },
  {
    title: t('admin.operations'),
    links: [
      { label: t('admin.inventory'), to: cr('inventory'), icon: Boxes, area: 'inventory' },
      { label: t('admin.shipping'), to: cr('shipping'), icon: Truck, area: 'shipping' },
      { label: t('admin.procurement'), to: cr('procurement'), icon: Building2, area: 'shipping' },
      { label: t('admin.pricing'), to: cr('pricing'), icon: Layers, area: 'marketing' },
      { label: t('admin.fraud'), to: cr('fraud'), icon: ShieldAlert, area: 'finance' }
    ]
  },
  {
    title: t('admin.finance'),
    links: [
      { label: t('admin.payouts'), to: cr('payouts'), icon: Wallet, area: 'finance' },
      { label: t('admin.finance'), to: cr('finance'), icon: Landmark, area: 'finance' }
    ]
  },
  {
    title: t('admin.store'),
    links: [
      { label: t('admin.notifications'), to: cr('notifications'), icon: Bell, area: 'settings' },
      ...(tenant.canManageMembers ? [{ label: t('admin.team'), to: cr('team'), icon: Users }] : []),
      { label: t('admin.settings'), to: cr('settings'), icon: Settings, area: 'settings' }
    ]
  }
]);

// Filter links by the caller's granted areas, then drop groups left empty.
const filteredStoreGroups = computed(() =>
  storeGroups.value
    .map((g) => ({ ...g, links: g.links.filter((l) => l.area == null || tenant.canArea(l.area)) }))
    .filter((g) => g.links.length)
);

// Which nav to show: the admin sees the platform panel until they enter a store.
const navGroups = computed(() => (inStore.value ? filteredStoreGroups.value : platformGroups.value));

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
  // Land on the selected store's dashboard (a full reload gives fresh,
  // store-scoped state). The admin thereby "enters" any store as its owner.
  const dash = cr('dashboard');
  if (router.currentRoute.value.name === dash.name) router.go(0);
  else router.push(dash).then(() => router.go(0)).catch(() => router.go(0));
};

// Admin leaves the current store and returns to the platform panel.
const backToPanel = () => {
  tenant.exitStore();
  storeMenu.value = false;
  router.push({ name: 'admin-platform' });
};

const logout = async () => {
  await auth.logout();
  router.push({ name: 'login' });
};

onMounted(() => tenant.ensureReady());
watch(() => router.currentRoute.value.fullPath, () => (sidebarOpen.value = false));
</script>

<template>
  <div class="min-h-screen bg-slate-100 text-ink dark:!bg-slate-950">
    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 start-0 z-40 flex w-64 flex-col border-e border-slate-200 bg-white transition-transform lg:!translate-x-0 dark:border-slate-800 dark:bg-slate-900"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full rtl:translate-x-full'"
    >
      <div class="flex h-16 items-center gap-2 border-b border-slate-100 px-4 dark:border-slate-800">
        <img :src="theme === 'dark' ? '/brand/dark-logo.png' : '/brand/qtech-logo.png'" alt="q-shop" class="h-9 w-auto" />
        <span class="font-heading text-sm font-bold text-slate-500">
          {{ isAdmin ? (inStore ? $t('admin.managingStore') : $t('admin.adminPanel')) : $t('admin.seller') }}
        </span>
      </div>

      <div class="space-y-2 border-b border-slate-100 p-3">
        <!-- Admin: leave the store and go back to the platform panel -->
        <button v-if="isAdmin && inStore" class="btn btn-outline btn-sm w-full justify-center" @click="backToPanel">
          <ArrowLeft class="h-4 w-4 rtl:rotate-180" /> {{ $t('admin.backToPanel') }}
        </button>

        <!-- Store switcher — sellers switch their own stores; the admin enters/switches any store -->
        <div class="relative">
          <button
            class="flex w-full items-center gap-3 rounded-lg border px-3 py-2 text-start hover:bg-slate-50"
            :class="isAdmin && !inStore ? 'border-dashed border-primary-300 bg-primary-50/40' : 'border-slate-200'"
            @click="storeMenu = !storeMenu"
          >
            <span class="grid h-8 w-8 place-items-center rounded-md text-xs font-bold" :class="activeStore ? 'bg-primary-100 text-primary-700' : 'bg-primary-50 text-primary-500'">
              <LogIn v-if="isAdmin && !inStore" class="h-4 w-4" />
              <template v-else>{{ (activeStore?.name || '?').charAt(0).toUpperCase() }}</template>
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-semibold">{{ activeStore?.name || (isAdmin ? $t('admin.enterStore') : $t('admin.selectStore')) }}</span>
              <span class="block truncate text-xs text-slate-400">{{ activeStore?.slug || (isAdmin && !inStore ? $t('admin.enterStoreHint') : '—') }}</span>
            </span>
            <ChevronDown class="h-4 w-4 text-slate-400" />
          </button>
          <div
            v-if="storeMenu"
            class="absolute z-10 mt-1 max-h-72 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white py-1 shadow-pop"
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
            <!-- Seller: create another store / request a higher cap -->
            <template v-if="!isAdmin && tenant.stores.length">
              <div class="my-1 border-t border-slate-100"></div>
              <button v-if="canCreateStore" class="dropdown-item w-full text-primary-600" @click="openCreateStore">
                <Plus class="h-4 w-4" /> {{ $t('storeSwitcher.newStore') }}
              </button>
              <button v-else class="dropdown-item w-full text-slate-600" @click="openStoreReq">
                <Send class="h-4 w-4" /> {{ $t('storeSwitcher.requestMore') }}
              </button>
              <p class="px-4 py-1 text-[11px] text-slate-400">
                {{ $t('storeSwitcher.yourStores') }}: <span dir="ltr">{{ tenant.stores.length }} / {{ maxStores }}</span>
              </p>
            </template>
            <!-- Admin: exit back to the platform panel -->
            <template v-if="isAdmin && inStore">
              <div class="my-1 border-t border-slate-100"></div>
              <button class="dropdown-item w-full text-slate-600" @click="backToPanel">
                <ArrowLeft class="h-4 w-4 rtl:rotate-180" /> {{ $t('admin.backToPanel') }}
              </button>
            </template>
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
      <header class="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur lg:px-8 dark:border-slate-800 dark:bg-slate-900/90">
        <button
          class="grid h-10 w-10 place-items-center rounded-lg hover:bg-slate-100 lg:hidden"
          @click="sidebarOpen = true"
        >
          <Menu class="h-5 w-5" />
        </button>
        <div class="ms-auto flex items-center gap-3">
          <button
            class="grid h-10 w-10 place-items-center rounded-lg text-ink hover:bg-slate-100 dark:hover:bg-slate-800"
            :title="orderSoundMuted ? $t('orderAlerts.soundOff') : $t('orderAlerts.soundOn')"
            :aria-label="orderSoundMuted ? $t('orderAlerts.soundOff') : $t('orderAlerts.soundOn')"
            @click="toggleOrderSound"
          >
            <component :is="orderSoundMuted ? VolumeX : Volume2" class="h-5 w-5" :class="orderSoundMuted ? 'text-slate-400' : 'text-primary-600'" />
          </button>
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

    <!-- Seller: create another store (within the admin-set cap) -->
    <Modal v-model="showCreateStore" :title="$t('storeSwitcher.newStore')">
      <form id="new-store-form" class="grid gap-4" novalidate @submit.prevent="createStore">
        <FormField v-model="storeForm.name" :label="$t('storeSwitcher.storeName')" :error="csErr.name" @update:model-value="clearCs('name')" />
        <FormField v-model="storeForm.country" :label="$t('common.country')" placeholder="EG" :error="csErr.country" @update:model-value="clearCs('country')" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showCreateStore = false">{{ $t('common.cancel') }}</button>
          <button form="new-store-form" type="submit" class="btn btn-primary" :disabled="creatingStore">
            <Spinner v-if="creatingStore" :size="18" /><span v-else>{{ $t('common.create') }}</span>
          </button>
        </div>
      </template>
    </Modal>

    <!-- Seller: request a higher store cap -->
    <Modal v-model="showStoreReq" :title="$t('storeSwitcher.requestMore')" size="sm">
      <form id="store-req-form" class="grid gap-3" novalidate @submit.prevent="requestStores">
        <p class="text-sm text-muted">{{ $t('storeSwitcher.requestHint', { current: maxStores }) }}</p>
        <FormField v-model.number="storeReqForm.requested_limit" :label="$t('storeSwitcher.maxStores')" type="number" min="1" :error="srErr.requested_limit" @update:model-value="clearSr('requested_limit')" />
        <FormField v-model="storeReqForm.note" :label="$t('team.requestNote')" :placeholder="$t('team.requestNotePlaceholder')" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showStoreReq = false">{{ $t('common.cancel') }}</button>
          <button form="store-req-form" type="submit" class="btn btn-primary" :disabled="storeReqBusy">
            <Spinner v-if="storeReqBusy" :size="18" /><span v-else>{{ $t('team.sendRequest') }}</span>
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
