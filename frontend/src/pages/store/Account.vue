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
  Plus
} from 'lucide-vue-next';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Spinner from '@/components/ui/Spinner.vue';
import PageHero from '@/components/ui/PageHero.vue';
import Alert from '@/components/ui/Alert.vue';
import FormField from '@/components/ui/FormField.vue';
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
  { key: 'addresses', label: 'Addresses', icon: MapPin },
  { key: 'wishlist', label: 'Wishlist', icon: Heart },
  { key: 'security', label: 'Security', icon: ShieldCheck }
];
const tab = ref('profile');

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
    ui.success('Address removed.');
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
    ui.success('Moved to cart.');
  } catch (e) {
    ui.error(errorMessage(e));
  }
};

// --- Security -------------------------------------------------------------
const pwd = ref({ current_password: '', new_password: '', new_password_confirm: '' });
const pwdBusy = ref(false);
const changePassword = async () => {
  pwdBusy.value = true;
  try {
    await apiPost('/auth/password/change/', pwd.value);
    ui.success('Password changed. Please sign in again.');
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
};

onMounted(() => {
  if (!auth.user) auth.loadProfile();
});
</script>

<template>
  <div>
    <PageHero title="My Account" :items="[{ label: 'Account' }]" />
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
            <component :is="t.icon" class="h-5 w-5" /> {{ t.label }}
          </button>
          <button class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50" @click="logout">
            <LogOut class="h-5 w-5" /> Sign out
          </button>
        </nav>
      </aside>

      <!-- Content -->
      <div>
        <Alert v-if="!hasStore && tab !== 'profile' && tab !== 'security'" variant="info" class="mb-5">
          Visit a store to see your store-specific orders, addresses and wishlist.
          <RouterLink :to="{ name: 'stores' }" class="font-semibold underline">Browse stores</RouterLink>
        </Alert>

        <!-- Profile -->
        <section v-if="tab === 'profile'" class="card p-6">
          <h2 class="section-title mb-4">Profile</h2>
          <dl class="grid gap-4 sm:grid-cols-2">
            <div><dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Email</dt><dd class="mt-1 font-medium">{{ auth.user?.email }}</dd></div>
            <div>
              <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Status</dt>
              <dd class="mt-1"><StatusBadge :status="auth.user?.is_verified ? 'active' : 'pending'" :label="auth.user?.is_verified ? 'Verified' : 'Unverified'" /></dd>
            </div>
            <div><dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Member since</dt><dd class="mt-1 font-medium">{{ (auth.user?.created_at || '').slice(0, 10) }}</dd></div>
            <div><dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Account type</dt><dd class="mt-1 font-medium">{{ auth.user?.is_staff ? 'Staff' : 'Customer' }}</dd></div>
          </dl>
          <div class="mt-6 border-t border-slate-100 pt-6">
            <RouterLink :to="{ name: 'admin-dashboard' }" class="btn btn-outline btn-sm">Go to seller dashboard</RouterLink>
          </div>
        </section>

        <!-- Orders -->
        <section v-else-if="tab === 'orders'">
          <div v-if="ordersLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" label="Loading orders…" /></div>
          <div v-else-if="orders.length" class="space-y-4">
            <div v-for="o in orders" :key="o.id" class="card p-5">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="font-semibold">Order #{{ o.number }}</p>
                  <p class="text-xs text-slate-400">{{ (o.placed_at || o.created_at || '').slice(0, 10) }} · {{ o.items?.length || 0 }} items</p>
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
            </div>
          </div>
          <EmptyState v-else :icon="ShoppingBag" title="No orders yet" message="When you place an order, it will appear here.">
            <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-sm">Start shopping</RouterLink>
          </EmptyState>
        </section>

        <!-- Addresses -->
        <section v-else-if="tab === 'addresses'">
          <div v-if="addressesLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" label="Loading addresses…" /></div>
          <div v-else-if="addresses.length" class="grid gap-4 sm:grid-cols-2">
            <div v-for="a in addresses" :key="a.id" class="card p-5">
              <div class="flex items-start justify-between">
                <div>
                  <p class="font-semibold">{{ a.full_name }}</p>
                  <span class="chip mt-1 border-slate-200 text-slate-500">{{ a.label }}</span>
                </div>
                <span v-if="a.is_default" class="chip border-primary-200 bg-primary-50 text-primary-700">Default</span>
              </div>
              <div class="mt-3 text-sm text-slate-500">
                <p>{{ a.line1 }}<span v-if="a.line2">, {{ a.line2 }}</span></p>
                <p>{{ a.city }}, {{ a.region }} {{ a.postal_code }}</p>
                <p>{{ a.country }} · {{ a.phone }}</p>
              </div>
              <div class="mt-4 flex gap-2">
                <button v-if="!a.is_default" class="btn btn-ghost btn-sm" @click="makeDefault(a.id)">Set default</button>
                <button class="btn btn-ghost btn-sm text-rose-600" @click="deleteAddress(a.id)"><Trash2 class="h-4 w-4" /> Remove</button>
              </div>
            </div>
          </div>
          <EmptyState v-else :icon="MapPin" title="No saved addresses" message="Add an address during checkout and it will be saved here." />
        </section>

        <!-- Wishlist -->
        <section v-else-if="tab === 'wishlist'">
          <div v-if="wishlistLoading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" label="Loading wishlist…" /></div>
          <div v-else-if="wishlist.length" class="grid gap-4 sm:grid-cols-2">
            <div v-for="w in wishlist" :key="w.id" class="card flex gap-4 p-4">
              <img :src="productImage({ id: w.variant })" :alt="w.product_name" class="h-20 w-20 rounded-lg object-cover" @error="onImgError" />
              <div class="flex flex-1 flex-col">
                <p class="font-semibold">{{ w.product_name }}</p>
                <p class="text-sm text-slate-500">{{ w.unit_price }} {{ currency }}</p>
                <div class="mt-auto flex gap-2 pt-2">
                  <button class="btn btn-primary btn-sm" @click="moveWishToCart(w.id)"><Plus class="h-4 w-4" /> Add to cart</button>
                  <button class="btn btn-ghost btn-sm text-rose-600" @click="removeWish(w.id)"><Trash2 class="h-4 w-4" /></button>
                </div>
              </div>
            </div>
          </div>
          <EmptyState v-else :icon="Heart" title="Your wishlist is empty" message="Save products you love to buy them later." />
        </section>

        <!-- Security -->
        <section v-else-if="tab === 'security'" class="card max-w-lg p-6">
          <h2 class="section-title mb-4">Change password</h2>
          <form class="space-y-4" @submit.prevent="changePassword">
            <FormField v-model="pwd.current_password" label="Current password" type="password" autocomplete="current-password" required />
            <FormField v-model="pwd.new_password" label="New password" type="password" autocomplete="new-password" required />
            <FormField v-model="pwd.new_password_confirm" label="Confirm new password" type="password" autocomplete="new-password" required />
            <button type="submit" class="btn btn-primary" :disabled="pwdBusy">
              <Spinner v-if="pwdBusy" :size="18" /><span v-else>Update password</span>
            </button>
          </form>
        </section>
      </div>
    </div>
    </div>
  </div>
</template>
