<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  User,
  ShoppingBag,
  MapPin,
  Heart,
  ShieldCheck,
  LogOut,
  Trash2,
  Plus,
  Gift,
  Undo2,
  MonitorSmartphone,
  Wallet,
  Ticket,
  Download,
  Share2,
  Copy,
  Palette,
  Sun,
  Moon,
  Languages
} from 'lucide-vue-next';
import { useI18n } from '@/i18n';
import { useTheme } from '@/theme';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Spinner from '@/components/ui/Spinner.vue';
import PageHero from '@/components/ui/PageHero.vue';
import Alert from '@/components/ui/Alert.vue';
import FormField from '@/components/ui/FormField.vue';
import Modal from '@/components/ui/Modal.vue';
import { useAuthStore } from '@/stores/auth';
import { useCartStore } from '@/stores/cart';
import { useUiStore } from '@/stores/ui';
import { shop } from '@/services/shop';
import { apiPost, errorMessage } from '@/services/http';
import { productImage, onImgError } from '@/utils/media';

const router = useRouter();
const auth = useAuthStore();
const cart = useCartStore();
const ui = useUiStore();

const tabs = [
  { key: 'profile', label: 'Profile', icon: User },
  { key: 'orders', label: 'Orders', icon: ShoppingBag },
  { key: 'returns', label: 'Returns', icon: Undo2 },
  { key: 'addresses', label: 'Addresses', icon: MapPin },
  { key: 'wishlist', label: 'Wishlist', icon: Heart },
  { key: 'downloads', label: 'Downloads', icon: Download },
  { key: 'rewards', label: 'Rewards', icon: Gift },
  { key: 'referrals', label: 'Referrals', icon: Share2 },
  { key: 'sessions', label: 'Sessions', icon: MonitorSmartphone },
  { key: 'preferences', label: 'Preferences', icon: Palette },
  { key: 'security', label: 'Security', icon: ShieldCheck }
];
const tab = ref('profile');
const { t, locale, setLocale } = useI18n();
const { theme, setTheme } = useTheme();

const hasStore = computed(() => Boolean(cart.shopStore));
const currency = computed(() => cart.shopStore?.currency || '');

// --- Orders ---------------------------------------------------------------
const orders = ref([]);
const ordersLoading = ref(false);
const loadOrders = async () => {
  if (!hasStore.value) return;
  ordersLoading.value = true;
  try {
    const res = await shop.orders(cart.headers);
    orders.value = res.data?.results || res.data || [];
  } finally {
    ordersLoading.value = false;
  }
};

// --- Addresses ------------------------------------------------------------
const addresses = ref([]);
const addressesLoading = ref(false);
const loadAddresses = async () => {
  if (!hasStore.value) return;
  addressesLoading.value = true;
  try {
    const res = await shop.addresses(cart.headers);
    addresses.value = res.data?.results || res.data || [];
  } finally {
    addressesLoading.value = false;
  }
};
const deleteAddress = async (id) => {
  try {
    await shop.deleteAddress(cart.headers, id);
    addresses.value = addresses.value.filter((a) => a.id !== id);
    ui.success(t('account.addressRemoved'));
  } catch (e) {
    ui.error(errorMessage(e));
  }
};
const makeDefault = async (id) => {
  try {
    await shop.setDefaultAddress(cart.headers, id);
    addresses.value = addresses.value.map((a) => ({ ...a, is_default: a.id === id }));
  } catch (e) {
    ui.error(errorMessage(e));
  }
};

// --- Wishlist -------------------------------------------------------------
const wishlist = ref([]);
const wishlistLoading = ref(false);
const loadWishlist = async () => {
  if (!hasStore.value) return;
  wishlistLoading.value = true;
  try {
    const res = await shop.wishlist(cart.headers);
    wishlist.value = res.data?.results || res.data || [];
  } finally {
    wishlistLoading.value = false;
  }
};
const removeWish = async (id) => {
  try {
    await shop.removeWishlist(cart.headers, id);
    wishlist.value = wishlist.value.filter((w) => w.id !== id);
  } catch (e) {
    ui.error(errorMessage(e));
  }
};
const moveWishToCart = async (id) => {
  try {
    await shop.wishlistToCart(cart.headers, id);
    wishlist.value = wishlist.value.filter((w) => w.id !== id);
    await cart.refreshCart();
    ui.success(t('account.movedToCart'));
  } catch (e) {
    ui.error(errorMessage(e));
  }
};

// --- Rewards --------------------------------------------------------------
const wallet = ref(null);
const points = ref(0);
const rewardsLoading = ref(false);
const giftCode = ref('');
const redeemPts = ref(0);
const rewardBusy = ref(false);
const loadRewards = async () => {
  if (!hasStore.value) return;
  rewardsLoading.value = true;
  try {
    const [w, l] = await Promise.all([shop.wallet(cart.headers), shop.loyalty(cart.headers)]);
    wallet.value = w.data;
    points.value = l.data?.points || 0;
  } catch {
    wallet.value = null;
  } finally {
    rewardsLoading.value = false;
  }
};
const redeemGift = async () => {
  if (!giftCode.value.trim()) return;
  rewardBusy.value = true;
  try {
    const r = await shop.redeemGiftCard(cart.headers, { code: giftCode.value.trim() });
    ui.success(t('account.giftRedeemed', { amount: r.data.redeemed, currency: currency.value }));
    giftCode.value = '';
    loadRewards();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    rewardBusy.value = false;
  }
};
const redeemPoints = async () => {
  if (redeemPts.value < 1) return;
  rewardBusy.value = true;
  try {
    const r = await shop.redeemLoyalty(cart.headers, { points: redeemPts.value });
    ui.success(t('account.pointsRedeemed', { points: r.data.points_redeemed, credit: r.data.wallet_credit, currency: currency.value }));
    redeemPts.value = 0;
    loadRewards();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    rewardBusy.value = false;
  }
};

// --- Returns --------------------------------------------------------------
const returns = ref([]);
const returnsLoading = ref(false);
const loadReturns = async () => {
  if (!hasStore.value) return;
  returnsLoading.value = true;
  try {
    const res = await shop.returns(cart.headers);
    returns.value = res.data?.results || res.data || [];
  } catch {
    returns.value = [];
  } finally {
    returnsLoading.value = false;
  }
};
const returnModal = ref(false);
const returnOrder = ref(null);
const returnReason = ref('');
const returnBusy = ref(false);
const openReturn = (order) => {
  returnOrder.value = order;
  returnReason.value = '';
  returnModal.value = true;
};
const submitReturn = async () => {
  returnBusy.value = true;
  try {
    await shop.createReturn(cart.headers, {
      order_id: returnOrder.value.id,
      reason: returnReason.value,
      resolution: 'refund',
      items: (returnOrder.value.items || []).map((it) => ({
        order_item_id: it.id,
        quantity: it.quantity,
        reason: returnReason.value
      }))
    });
    ui.success(t('account.returnRequested'));
    returnModal.value = false;
    loadReturns();
    if (tab.value !== 'returns') selectTab('returns');
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    returnBusy.value = false;
  }
};

// --- Sessions & notification preferences ----------------------------------
const devices = ref([]);
const devicesLoading = ref(false);
const prefs = ref(null);
const loadSessions = async () => {
  devicesLoading.value = true;
  try {
    const res = await shop.devices();
    devices.value = res.data?.results || res.data || [];
  } catch {
    devices.value = [];
  } finally {
    devicesLoading.value = false;
  }
  if (hasStore.value) {
    try {
      const p = await shop.notificationPrefs(cart.headers);
      prefs.value = p.data;
    } catch {
      prefs.value = null;
    }
  }
};
const revokeDevice = async (id) => {
  try {
    await shop.revokeDevice(id);
    devices.value = devices.value.filter((d) => d.id !== id);
    ui.success(t('account.sessionRevoked'));
  } catch (e) {
    ui.error(errorMessage(e));
  }
};
const revokeAll = async () => {
  try {
    await shop.revokeAllDevices();
    ui.success(t('account.allSessionsRevoked'));
    loadSessions();
  } catch (e) {
    ui.error(errorMessage(e));
  }
};
const savePrefs = async () => {
  try {
    const p = await shop.updateNotificationPrefs(cart.headers, prefs.value);
    prefs.value = p.data;
    ui.success(t('account.prefsSaved'));
  } catch (e) {
    ui.error(errorMessage(e));
  }
};

// --- Downloads ------------------------------------------------------------
const downloads = ref([]);
const downloadsLoading = ref(false);
const loadDownloads = async () => {
  if (!hasStore.value) return;
  downloadsLoading.value = true;
  try {
    const res = await shop.downloads(cart.headers);
    downloads.value = res.data?.results || res.data || [];
  } catch {
    downloads.value = [];
  } finally {
    downloadsLoading.value = false;
  }
};

// --- Referrals ------------------------------------------------------------
const referralStats = ref(null);
const referralList = ref([]);
const referralsLoading = ref(false);
const applyCode = ref('');
const applyBusy = ref(false);
const loadReferrals = async () => {
  if (!hasStore.value) return;
  referralsLoading.value = true;
  try {
    const [s, l] = await Promise.all([shop.referralStats(cart.headers), shop.referrals(cart.headers)]);
    referralStats.value = s.data;
    referralList.value = l.data?.results || l.data || [];
  } catch {
    referralStats.value = null;
  } finally {
    referralsLoading.value = false;
  }
};
const copyCode = async () => {
  const code = referralStats.value?.code;
  if (!code) return;
  try {
    await navigator.clipboard.writeText(code);
    ui.success(t('account.codeCopied'));
  } catch {
    ui.info(code);
  }
};
const applyReferral = async () => {
  if (!applyCode.value.trim()) return;
  applyBusy.value = true;
  try {
    await shop.applyReferral(cart.headers, { code: applyCode.value.trim() });
    ui.success(t('account.codeApplied'));
    applyCode.value = '';
    loadReferrals();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    applyBusy.value = false;
  }
};

// --- Security -------------------------------------------------------------
const pwd = ref({ current_password: '', new_password: '', new_password_confirm: '' });
const pwdBusy = ref(false);
const changePassword = async () => {
  pwdBusy.value = true;
  try {
    await apiPost('/auth/password/change/', pwd.value);
    ui.success(t('account.passwordChanged'));
    pwd.value = { current_password: '', new_password: '', new_password_confirm: '' };
    await auth.logout();
    router.push({ name: 'login' });
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    pwdBusy.value = false;
  }
};

const logout = async () => {
  await auth.logout();
  router.push({ name: 'home' });
};

const selectTab = (key) => {
  tab.value = key;
  if (key === 'orders' && !orders.value.length) loadOrders();
  if (key === 'addresses' && !addresses.value.length) loadAddresses();
  if (key === 'wishlist' && !wishlist.value.length) loadWishlist();
  if (key === 'returns' && !returns.value.length) loadReturns();
  if (key === 'rewards' && !wallet.value) loadRewards();
  if (key === 'sessions' && !devices.value.length) loadSessions();
  if (key === 'downloads' && !downloads.value.length) loadDownloads();
  if (key === 'referrals' && !referralStats.value) loadReferrals();
};

onMounted(() => {
  if (!auth.user) auth.loadProfile();
});
</script>

<template>
  <div>
    <PageHero :title="$t('account.title')" :items="[{ label: $t('nav.account') }]" />
    <div class="container py-10">

    <div class="grid gap-8 lg:grid-cols-[240px_1fr]">
      <!-- Sidebar -->
      <aside class="card h-fit p-3">
        <div class="flex items-center gap-3 border-b border-slate-100 p-3">
          <span class="grid h-11 w-11 place-items-center rounded-full bg-primary-100 text-lg font-bold text-primary-700">
            {{ auth.displayName.charAt(0).toUpperCase() }}
          </span>
          <div class="min-w-0">
            <p class="truncate font-semibold">{{ auth.displayName }}</p>
            <p class="truncate text-xs text-slate-500">{{ auth.user?.email }}</p>
          </div>
        </div>
        <nav class="mt-2 space-y-1">
          <button
            v-for="t in tabs"
            :key="t.key"
            class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition"
            :class="tab === t.key ? 'bg-primary-50 text-primary-700' : 'text-slate-600 hover:bg-slate-100'"
            @click="selectTab(t.key)"
          >
            <component :is="t.icon" class="h-5 w-5" /> {{ $t('account.' + t.key) }}
          </button>
          <button class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50" @click="logout">
            <LogOut class="h-5 w-5" /> {{ $t('account.signOut') }}
          </button>
        </nav>
      </aside>

      <!-- Content -->
      <div>
        <Alert v-if="!hasStore && !['profile', 'security', 'sessions'].includes(tab)" variant="info" class="mb-5">
          {{ $t('account.storeAlert') }}
          <RouterLink :to="{ name: 'stores' }" class="font-semibold underline">{{ $t('account.browseStores') }}</RouterLink>
        </Alert>

        <!-- Profile -->
        <section v-if="tab === 'profile'" class="card p-6">
          <h2 class="section-title mb-4">{{ $t('account.profile') }}</h2>
          <dl class="grid gap-4 sm:grid-cols-2">
            <div><dt class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ $t('common.email') }}</dt><dd class="mt-1 font-medium">{{ auth.user?.email }}</dd></div>
            <div>
              <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ $t('common.status') }}</dt>
              <dd class="mt-1"><StatusBadge :status="auth.user?.is_verified ? 'active' : 'pending'" :label="auth.user?.is_verified ? $t('account.verified') : $t('account.unverified')" /></dd>
            </div>
            <div><dt class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ $t('account.memberSince') }}</dt><dd class="mt-1 font-medium">{{ (auth.user?.created_at || '').slice(0, 10) }}</dd></div>
            <div><dt class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ $t('account.accountType') }}</dt><dd class="mt-1 font-medium">{{ auth.user?.is_staff ? $t('account.staff') : $t('account.customer') }}</dd></div>
          </dl>
          <div class="mt-6 border-t border-slate-100 pt-6">
            <RouterLink :to="{ name: 'admin-dashboard' }" class="btn btn-outline btn-sm">{{ $t('account.sellerDashboard') }}</RouterLink>
          </div>
        </section>

        <!-- Orders -->
        <section v-else-if="tab === 'orders'">
          <div v-if="ordersLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" :label="$t('account.loadingOrders')" /></div>
          <div v-else-if="orders.length" class="space-y-4">
            <div v-for="o in orders" :key="o.id" class="card p-5">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="font-semibold">{{ $t('account.orderNum') }} #{{ o.number }}</p>
                  <p class="text-xs text-slate-400">{{ (o.placed_at || o.created_at || '').slice(0, 10) }} · {{ o.items?.length || 0 }} {{ $t('account.itemsWord') }}</p>
                </div>
                <div class="flex items-center gap-4">
                  <StatusBadge :status="o.status" />
                  <span class="font-bold">{{ o.total }} {{ o.currency }}</span>
                </div>
              </div>
              <ul class="mt-3 border-t border-slate-100 pt-3 text-sm text-slate-600">
                <li v-for="it in o.items" :key="it.id" class="flex justify-between py-1">
                  <span>{{ it.product_name }} <span class="text-slate-400">× {{ it.quantity }}</span></span>
                  <span>{{ it.line_total }} {{ o.currency }}</span>
                </li>
              </ul>
              <div class="mt-3 flex justify-end gap-2">
                <RouterLink :to="{ name: 'order-confirmation', params: { id: o.id } }" class="btn btn-ghost btn-sm">{{ $t('common.view') }}</RouterLink>
                <button class="btn btn-outline btn-sm" @click="openReturn(o)"><Undo2 class="h-4 w-4" /> {{ $t('account.requestReturn') }}</button>
              </div>
            </div>
          </div>
          <EmptyState v-else :icon="ShoppingBag" :title="$t('account.noOrders')" :message="$t('account.noOrdersMsg')">
            <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-sm">{{ $t('cart.startShopping') }}</RouterLink>
          </EmptyState>
        </section>

        <!-- Addresses -->
        <section v-else-if="tab === 'addresses'">
          <div v-if="addressesLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" :label="$t('account.loadingAddresses')" /></div>
          <div v-else-if="addresses.length" class="grid gap-4 sm:grid-cols-2">
            <div v-for="a in addresses" :key="a.id" class="card p-5">
              <div class="flex items-start justify-between">
                <div>
                  <p class="font-semibold">{{ a.full_name }}</p>
                  <span class="chip mt-1 border-slate-200 text-slate-500">{{ a.label }}</span>
                </div>
                <span v-if="a.is_default" class="chip border-primary-200 bg-primary-50 text-primary-700">{{ $t('account.defaultLabel') }}</span>
              </div>
              <div class="mt-3 text-sm text-slate-500">
                <p>{{ a.line1 }}<span v-if="a.line2">, {{ a.line2 }}</span></p>
                <p>{{ a.city }}, {{ a.region }} {{ a.postal_code }}</p>
                <p>{{ a.country }} · {{ a.phone }}</p>
              </div>
              <div class="mt-4 flex gap-2">
                <button v-if="!a.is_default" class="btn btn-ghost btn-sm" @click="makeDefault(a.id)">{{ $t('account.setDefault') }}</button>
                <button class="btn btn-ghost btn-sm text-rose-600" @click="deleteAddress(a.id)"><Trash2 class="h-4 w-4" /> {{ $t('common.remove') }}</button>
              </div>
            </div>
          </div>
          <EmptyState v-else :icon="MapPin" :title="$t('account.noAddresses')" :message="$t('account.noAddressesMsg')" />
        </section>

        <!-- Wishlist -->
        <section v-else-if="tab === 'wishlist'">
          <div v-if="wishlistLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" :label="$t('account.loadingWishlist')" /></div>
          <div v-else-if="wishlist.length" class="grid gap-4 sm:grid-cols-2">
            <div v-for="w in wishlist" :key="w.id" class="card flex gap-4 p-4">
              <img :src="productImage({ id: w.variant })" :alt="w.product_name" class="h-20 w-20 rounded-lg object-cover" @error="onImgError" />
              <div class="flex flex-1 flex-col">
                <p class="font-semibold">{{ w.product_name }}</p>
                <p class="text-sm text-slate-500">{{ w.unit_price }} {{ currency }}</p>
                <div class="mt-auto flex gap-2 pt-2">
                  <button class="btn btn-primary btn-sm" @click="moveWishToCart(w.id)"><Plus class="h-4 w-4" /> {{ $t('product.addToCart') }}</button>
                  <button class="btn btn-ghost btn-sm text-rose-600" @click="removeWish(w.id)"><Trash2 class="h-4 w-4" /></button>
                </div>
              </div>
            </div>
          </div>
          <EmptyState v-else :icon="Heart" :title="$t('account.wishlistEmpty')" :message="$t('account.wishlistEmptyMsg')" />
        </section>

        <!-- Returns -->
        <section v-else-if="tab === 'returns'">
          <div v-if="returnsLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" :label="$t('account.loadingReturns')" /></div>
          <div v-else-if="returns.length" class="space-y-4">
            <div v-for="r in returns" :key="r.id" class="card p-5">
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-semibold">{{ $t('account.returnLabel') }} · {{ $t('status.' + r.resolution) === 'status.' + r.resolution ? String(r.resolution).replace(/_/g, ' ') : $t('status.' + r.resolution) }}</p>
                  <p class="text-xs text-slate-400">{{ (r.created_at || '').slice(0, 10) }} · {{ r.items?.length || 0 }} {{ $t('account.itemsWord') }}</p>
                </div>
                <StatusBadge :status="r.status" />
              </div>
              <p v-if="r.reason" class="mt-2 text-sm text-slate-600">{{ r.reason }}</p>
              <p v-if="Number(r.refund_amount) > 0" class="mt-1 text-sm font-medium text-emerald-600">{{ $t('account.refund') }}: {{ r.refund_amount }} {{ currency }}</p>
            </div>
          </div>
          <EmptyState v-else :icon="Undo2" :title="$t('account.noReturns')" :message="$t('account.noReturnsMsg')" />
        </section>

        <!-- Rewards -->
        <section v-else-if="tab === 'rewards'">
          <div v-if="rewardsLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" :label="$t('account.loadingRewards')" /></div>
          <template v-else>
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="card flex items-center gap-4 p-5">
                <span class="grid h-12 w-12 place-items-center rounded-lg bg-emerald-50 text-emerald-600"><Wallet class="h-6 w-6" /></span>
                <div><p class="font-heading text-2xl font-bold">{{ wallet?.balance || '0.00' }} {{ currency }}</p><p class="text-sm text-muted">{{ $t('account.walletBalance') }}</p></div>
              </div>
              <div class="card flex items-center gap-4 p-5">
                <span class="grid h-12 w-12 place-items-center rounded-lg bg-primary-50 text-primary-600"><Gift class="h-6 w-6" /></span>
                <div><p class="font-heading text-2xl font-bold">{{ points }}</p><p class="text-sm text-muted">{{ $t('account.loyaltyPoints') }}</p></div>
              </div>
            </div>
            <div class="mt-4 grid gap-4 sm:grid-cols-2">
              <div class="card p-5">
                <h3 class="mb-3 flex items-center gap-2 font-semibold"><Ticket class="h-5 w-5 text-primary-600" /> {{ $t('account.redeemGift') }}</h3>
                <form class="flex gap-2" @submit.prevent="redeemGift">
                  <input v-model="giftCode" class="input" :placeholder="$t('account.giftCardCode')" />
                  <button class="btn btn-primary btn-sm shrink-0" :disabled="rewardBusy || !giftCode.trim()">{{ $t('account.redeem') }}</button>
                </form>
              </div>
              <div class="card p-5">
                <h3 class="mb-3 flex items-center gap-2 font-semibold"><Gift class="h-5 w-5 text-primary-600" /> {{ $t('account.redeemPoints') }}</h3>
                <form class="flex gap-2" @submit.prevent="redeemPoints">
                  <input v-model.number="redeemPts" type="number" min="1" class="input" :placeholder="$t('account.pointsPlaceholder')" />
                  <button class="btn btn-primary btn-sm shrink-0" :disabled="rewardBusy || redeemPts < 1">{{ $t('account.redeem') }}</button>
                </form>
              </div>
            </div>
            <div v-if="wallet?.transactions?.length" class="card mt-4 p-5">
              <h3 class="mb-3 font-semibold">{{ $t('account.walletActivity') }}</h3>
              <ul class="divide-y divide-slate-100 text-sm">
                <li v-for="t in wallet.transactions" :key="t.id" class="flex items-center justify-between py-2">
                  <span class="capitalize text-slate-600">{{ String(t.txn_type).replace(/_/g, ' ') }} <span class="text-xs text-slate-400">{{ (t.created_at || '').slice(0, 10) }}</span></span>
                  <span class="font-medium" :class="Number(t.amount) < 0 ? 'text-secondary-500' : 'text-emerald-600'">{{ Number(t.amount) > 0 ? '+' : '' }}{{ t.amount }} {{ currency }}</span>
                </li>
              </ul>
            </div>
          </template>
        </section>

        <!-- Downloads -->
        <section v-else-if="tab === 'downloads'">
          <div v-if="downloadsLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" :label="$t('account.loadingDownloads')" /></div>
          <div v-else-if="downloads.length" class="space-y-3">
            <div v-for="d in downloads" :key="d.id" class="card flex items-center justify-between p-4">
              <div class="flex items-center gap-3">
                <span class="grid h-10 w-10 place-items-center rounded-lg bg-primary-50 text-primary-600"><Download class="h-5 w-5" /></span>
                <div>
                  <p class="text-sm font-medium">{{ $t('account.digitalItem') }}</p>
                  <p class="text-xs text-slate-400">{{ d.download_count }}/{{ d.download_limit }} {{ $t('account.downloadsWord') }} · {{ d.remaining_downloads }} {{ $t('account.left') }}<span v-if="d.expires_at"> · {{ $t('account.expires') }} {{ (d.expires_at || '').slice(0, 10) }}</span></p>
                  <p v-if="d.license_keys?.length" class="mt-1 text-xs text-muted">{{ $t('account.keysLabel') }}: {{ d.license_keys.join(', ') }}</p>
                </div>
              </div>
              <a v-if="d.can_download && d.download_url" :href="d.download_url" target="_blank" rel="noopener" class="btn btn-primary btn-sm"><Download class="h-4 w-4" /> {{ $t('account.download') }}</a>
              <span v-else class="chip border-slate-200 text-slate-500">{{ $t('account.unavailable') }}</span>
            </div>
          </div>
          <EmptyState v-else :icon="Download" :title="$t('account.noDownloads')" :message="$t('account.noDownloadsMsg')" />
        </section>

        <!-- Referrals -->
        <section v-else-if="tab === 'referrals'">
          <div v-if="referralsLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" :label="$t('account.loadingReferrals')" /></div>
          <template v-else>
            <div class="card p-6">
              <h2 class="section-title mb-2">{{ $t('account.inviteFriends') }}</h2>
              <p class="text-sm text-muted">{{ $t('account.referralIntro') }}</p>
              <div class="mt-4 flex items-center gap-2">
                <code class="flex-1 rounded-lg border border-dashed border-primary-300 bg-primary-50 px-4 py-3 text-center font-mono text-lg font-bold text-primary-700">{{ referralStats?.code || '—' }}</code>
                <button class="btn btn-outline" :disabled="!referralStats?.code" @click="copyCode"><Copy class="h-4 w-4" /> {{ $t('account.copy') }}</button>
              </div>
              <div v-if="referralStats" class="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
                <template v-for="(v, k) in referralStats" :key="k">
                  <div v-if="k !== 'code' && typeof v !== 'object'" class="rounded-lg bg-lightbg p-3 text-center">
                    <p class="font-heading text-xl font-bold">{{ v }}</p>
                    <p class="text-xs capitalize text-muted">{{ String(k).replace(/_/g, ' ') }}</p>
                  </div>
                </template>
              </div>
            </div>

            <div class="card mt-4 p-6">
              <h3 class="mb-3 font-semibold">{{ $t('account.haveCode') }}</h3>
              <form class="flex gap-2" @submit.prevent="applyReferral">
                <input v-model="applyCode" class="input" :placeholder="$t('account.enterCode')" />
                <button class="btn btn-primary btn-sm shrink-0" :disabled="applyBusy || !applyCode.trim()">{{ $t('common.apply') }}</button>
              </form>
            </div>

            <div v-if="referralList.length" class="card mt-4 p-5">
              <h3 class="mb-3 font-semibold">{{ $t('account.yourReferrals') }}</h3>
              <ul class="divide-y divide-slate-100 text-sm">
                <li v-for="r in referralList" :key="r.id" class="flex items-center justify-between py-2">
                  <span>{{ r.referee_email || $t('account.friend') }}</span>
                  <StatusBadge :status="r.status" />
                </li>
              </ul>
            </div>
          </template>
        </section>

        <!-- Sessions -->
        <section v-else-if="tab === 'sessions'">
          <div v-if="devicesLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" :label="$t('account.loadingSessions')" /></div>
          <template v-else>
            <div class="mb-4 flex items-center justify-between">
              <h2 class="section-title">{{ $t('account.activeSessions') }}</h2>
              <button v-if="devices.length" class="btn btn-outline btn-sm" @click="revokeAll">{{ $t('account.signOutAll') }}</button>
            </div>
            <div v-if="devices.length" class="space-y-3">
              <div v-for="d in devices" :key="d.id" class="card flex items-center justify-between p-4">
                <div class="flex items-center gap-3">
                  <span class="grid h-10 w-10 place-items-center rounded-lg bg-primary-50 text-primary-600"><MonitorSmartphone class="h-5 w-5" /></span>
                  <div>
                    <p class="text-sm font-medium">{{ d.device_name || $t('account.device') }}</p>
                    <p class="text-xs text-slate-400">{{ d.ip_address }} · {{ (d.last_used_at || d.created_at || '').slice(0, 10) }}</p>
                  </div>
                </div>
                <button class="btn btn-ghost btn-sm text-secondary-500" @click="revokeDevice(d.id)"><Trash2 class="h-4 w-4" /> {{ $t('account.revoke') }}</button>
              </div>
            </div>
            <EmptyState v-else :icon="MonitorSmartphone" :title="$t('account.noSessions')" :message="$t('account.noSessionsMsg')" />

            <div v-if="prefs" class="card mt-6 max-w-lg p-6">
              <h2 class="section-title mb-4">{{ $t('account.notifPrefs') }}</h2>
              <label class="flex items-center gap-2 py-1.5 text-sm"><input v-model="prefs.in_app_enabled" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('account.inApp') }}</label>
              <label class="flex items-center gap-2 py-1.5 text-sm"><input v-model="prefs.email_enabled" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('account.emailNotif') }}</label>
              <button class="btn btn-primary btn-sm mt-3" @click="savePrefs">{{ $t('account.savePrefs') }}</button>
            </div>
          </template>
        </section>

        <!-- Preferences -->
        <section v-else-if="tab === 'preferences'" class="card max-w-lg p-6">
          <h2 class="section-title mb-5">{{ $t('account.preferences') }}</h2>
          <div class="space-y-6">
            <div>
              <p class="label mb-2">{{ $t('account.language') }}</p>
              <div class="flex gap-2">
                <button class="btn btn-sm" :class="locale === 'ar' ? 'btn-primary' : 'btn-outline'" @click="setLocale('ar')"><Languages class="h-4 w-4" /> {{ $t('account.arabic') }}</button>
                <button class="btn btn-sm" :class="locale === 'en' ? 'btn-primary' : 'btn-outline'" @click="setLocale('en')"><Languages class="h-4 w-4" /> {{ $t('account.english') }}</button>
              </div>
            </div>
            <div>
              <p class="label mb-2">{{ $t('account.theme') }}</p>
              <div class="flex gap-2">
                <button class="btn btn-sm" :class="theme === 'light' ? 'btn-primary' : 'btn-outline'" @click="setTheme('light')"><Sun class="h-4 w-4" /> {{ $t('account.light') }}</button>
                <button class="btn btn-sm" :class="theme === 'dark' ? 'btn-primary' : 'btn-outline'" @click="setTheme('dark')"><Moon class="h-4 w-4" /> {{ $t('account.dark') }}</button>
              </div>
            </div>
          </div>
        </section>

        <!-- Security -->
        <section v-else-if="tab === 'security'" class="card max-w-lg p-6">
          <h2 class="section-title mb-4">{{ $t('account.changePassword') }}</h2>
          <form class="space-y-4" @submit.prevent="changePassword">
            <FormField v-model="pwd.current_password" :label="$t('account.currentPassword')" type="password" autocomplete="current-password" required />
            <FormField v-model="pwd.new_password" :label="$t('account.newPassword')" type="password" autocomplete="new-password" required />
            <FormField v-model="pwd.new_password_confirm" :label="$t('account.confirmPassword')" type="password" autocomplete="new-password" required />
            <button type="submit" class="btn btn-primary" :disabled="pwdBusy">
              <Spinner v-if="pwdBusy" :size="18" /><span v-else>{{ $t('account.updatePassword') }}</span>
            </button>
          </form>
        </section>

        <!-- Request return modal -->
        <Modal v-model="returnModal" :title="returnOrder ? `${$t('account.returnLabel')} · ${$t('account.orderNum')} #${returnOrder.number}` : $t('account.requestReturnTitle')">
          <p class="mb-3 text-sm text-muted">{{ $t('account.returnModalMsg') }}</p>
          <ul class="mb-4 space-y-1 rounded-lg bg-lightbg p-3 text-sm">
            <li v-for="it in returnOrder?.items || []" :key="it.id" class="flex justify-between"><span>{{ it.product_name }}</span><span class="text-slate-400">× {{ it.quantity }}</span></li>
          </ul>
          <label class="label">{{ $t('account.reason') }}</label>
          <textarea v-model="returnReason" rows="3" class="input" :placeholder="$t('account.reasonPlaceholder')"></textarea>
          <template #footer>
            <div class="flex justify-end gap-2">
              <button class="btn btn-ghost" @click="returnModal = false">{{ $t('common.cancel') }}</button>
              <button class="btn btn-primary" :disabled="returnBusy" @click="submitReturn"><Spinner v-if="returnBusy" :size="18" /><span v-else>{{ $t('account.submitRequest') }}</span></button>
            </div>
          </template>
        </Modal>
      </div>
    </div>
    </div>
  </div>
</template>
