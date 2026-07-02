<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Minus, Plus, Trash2, ShoppingBag, Tag, ArrowRight, X } from 'lucide-vue-next';
import EmptyState from '@/components/ui/EmptyState.vue';
import Spinner from '@/components/ui/Spinner.vue';
import PageHero from '@/components/ui/PageHero.vue';
import { useAuthStore } from '@/stores/auth';
import { useCartStore } from '@/stores/cart';
import { useUiStore } from '@/stores/ui';
import { errorMessage } from '@/services/http';
import { productImage, onImgError } from '@/utils/media';

const router = useRouter();
const auth = useAuthStore();
const cart = useCartStore();
const ui = useUiStore();

const coupon = ref('');
const busyItem = ref(null);
const couponBusy = ref(false);

const currency = computed(() => cart.shopStore?.currency || '');
const data = computed(() => cart.cart);
const items = computed(() => data.value?.items || []);

const updateQty = async (item, quantity) => {
  if (quantity < 1) return;
  busyItem.value = item.id;
  try {
    await cart.updateItem(item.id, quantity);
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    busyItem.value = null;
  }
};

const remove = async (item) => {
  busyItem.value = item.id;
  try {
    await cart.removeItem(item.id);
    ui.success('Item removed.');
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    busyItem.value = null;
  }
};

const applyCoupon = async () => {
  if (!coupon.value.trim()) return;
  couponBusy.value = true;
  try {
    await cart.applyCoupon(coupon.value.trim());
    ui.success('Coupon applied.');
    coupon.value = '';
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    couponBusy.value = false;
  }
};

const removeCoupon = async () => {
  couponBusy.value = true;
  try {
    await cart.removeCoupon();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    couponBusy.value = false;
  }
};

onMounted(() => {
  if (auth.isAuthenticated) cart.refreshCart();
});
</script>

<template>
  <div>
    <PageHero title="Shopping Cart" :items="[{ label: 'Cart' }]" />
    <div class="container py-10">

    <div v-if="cart.loading && !data" class="flex min-h-[30vh] items-center justify-center">
      <Spinner :size="28" label="Loading cart…" />
    </div>

    <EmptyState
      v-else-if="!auth.isAuthenticated"
      :icon="ShoppingBag"
      title="Sign in to view your cart"
      message="Your cart is saved to your account so you can pick up where you left off."
    >
      <RouterLink :to="{ name: 'login', query: { redirect: '/cart' } }" class="btn btn-primary btn-sm">Sign in</RouterLink>
    </EmptyState>

    <EmptyState
      v-else-if="!items.length"
      :icon="ShoppingBag"
      title="Your cart is empty"
      message="Browse the marketplace and add products you love."
    >
      <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-sm">Start shopping</RouterLink>
    </EmptyState>

    <div v-else class="grid gap-8 lg:grid-cols-[1fr_360px]">
      <!-- Items -->
      <div class="space-y-4">
        <div v-if="cart.shopStore" class="text-sm text-slate-500">
          Shopping at <span class="font-semibold text-ink">{{ cart.shopStore.name }}</span>
        </div>
        <div v-for="item in items" :key="item.id" class="card flex gap-4 p-4">
          <img :src="productImage({ id: item.variant })" :alt="item.product_name" class="h-24 w-24 shrink-0 rounded-lg object-cover" @error="onImgError" />
          <div class="flex flex-1 flex-col">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="font-semibold">{{ item.product_name }}</p>
                <p class="text-xs text-slate-400">SKU: {{ item.sku }}</p>
              </div>
              <button class="text-slate-400 hover:text-rose-600" :disabled="busyItem === item.id" @click="remove(item)">
                <Trash2 class="h-4 w-4" />
              </button>
            </div>
            <div class="mt-auto flex items-end justify-between pt-3">
              <div class="inline-flex items-center rounded-lg border border-slate-200">
                <button class="grid h-8 w-8 place-items-center text-slate-600 hover:bg-slate-100 disabled:opacity-40" :disabled="item.quantity <= 1 || busyItem === item.id" @click="updateQty(item, item.quantity - 1)">
                  <Minus class="h-3.5 w-3.5" />
                </button>
                <span class="w-9 text-center text-sm font-semibold">{{ item.quantity }}</span>
                <button class="grid h-8 w-8 place-items-center text-slate-600 hover:bg-slate-100 disabled:opacity-40" :disabled="busyItem === item.id" @click="updateQty(item, item.quantity + 1)">
                  <Plus class="h-3.5 w-3.5" />
                </button>
              </div>
              <div class="text-right">
                <p class="font-bold">{{ item.line_total }} {{ currency }}</p>
                <p class="text-xs text-slate-400">{{ item.unit_price }} each</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Summary -->
      <aside class="h-fit space-y-4 lg:sticky lg:top-24">
        <div class="card p-5">
          <h3 class="font-semibold">Order summary</h3>

          <div class="mt-4">
            <div v-if="data.coupon_code" class="flex items-center justify-between rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
              <span class="flex items-center gap-1.5"><Tag class="h-4 w-4" /> {{ data.coupon_code }}</span>
              <button class="text-emerald-700 hover:text-emerald-900" :disabled="couponBusy" @click="removeCoupon"><X class="h-4 w-4" /></button>
            </div>
            <form v-else class="flex gap-2" @submit.prevent="applyCoupon">
              <input v-model="coupon" placeholder="Coupon code" class="input" />
              <button class="btn btn-outline btn-sm shrink-0" :disabled="couponBusy || !coupon.trim()">Apply</button>
            </form>
          </div>

          <dl class="mt-5 space-y-2 border-t border-slate-100 pt-4 text-sm">
            <div class="flex justify-between"><dt class="text-slate-500">Subtotal</dt><dd class="font-medium">{{ data.subtotal }} {{ currency }}</dd></div>
            <div v-if="Number(data.discount) > 0" class="flex justify-between text-emerald-600"><dt>Discount</dt><dd>−{{ data.discount }} {{ currency }}</dd></div>
            <div class="flex justify-between border-t border-slate-100 pt-2 text-base font-bold">
              <dt>Total</dt><dd>{{ data.total }} {{ currency }}</dd>
            </div>
          </dl>

          <RouterLink :to="{ name: 'checkout' }" class="btn btn-primary btn-lg mt-5 w-full">
            Checkout <ArrowRight class="h-4 w-4" />
          </RouterLink>
        </div>
        <RouterLink :to="{ name: 'products' }" class="block text-center text-sm font-medium text-primary-600 hover:underline">
          Continue shopping
        </RouterLink>
      </aside>
    </div>
    </div>
  </div>
</template>
