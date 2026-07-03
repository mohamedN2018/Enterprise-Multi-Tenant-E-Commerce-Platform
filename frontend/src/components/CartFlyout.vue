<script setup>
import { computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { X, Plus, Minus, Trash2, ShoppingBag, Check, ArrowRight, Truck } from 'lucide-vue-next';
import { useCartStore } from '@/stores/cart';
import { productImage, onImgError } from '@/utils/media';

const route = useRoute();
const router = useRouter();
const cart = useCartStore();

// Free-shipping qualifier threshold (Amazon-style progress hint).
const FREE_SHIP_THRESHOLD = 500;

const open = computed(() => cart.drawerOpen);
const data = computed(() => cart.cart);
const items = computed(() => data.value?.items || []);
const currency = computed(() => cart.shopStore?.currency || '');
const subtotal = computed(() => Number(data.value?.subtotal || 0));
const remaining = computed(() => Math.max(0, FREE_SHIP_THRESHOLD - subtotal.value));
const qualifies = computed(() => subtotal.value >= FREE_SHIP_THRESHOLD && subtotal.value > 0);
const progress = computed(() => Math.min(100, subtotal.value ? (subtotal.value / FREE_SHIP_THRESHOLD) * 100 : 0));

const close = () => cart.closeDrawer();
const goCart = () => {
  close();
  router.push({ name: 'cart' });
};
const goCheckout = () => {
  close();
  router.push({ name: 'checkout' });
};
const goShop = () => {
  close();
  router.push({ name: 'products' });
};

const updateQty = (item, q) => {
  if (q < 1) return cart.removeItem(item.id);
  cart.updateItem(item.id, q);
};

// Cart items may or may not carry a product id; only link when present.
const pid = (item) => item.product || item.product_id || null;

const onKey = (e) => {
  if (e.key === 'Escape' && open.value) close();
};

watch(open, (v) => {
  document.body.style.overflow = v ? 'hidden' : '';
});
watch(() => route.fullPath, () => cart.closeDrawer());
onMounted(() => window.addEventListener('keydown', onKey));
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey);
  document.body.style.overflow = '';
});
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open" class="fixed inset-0 z-[60] bg-slate-900/50 backdrop-blur-sm" @click="close"></div>
    </Transition>

    <aside
      class="fixed inset-y-0 end-0 z-[70] flex w-full max-w-[400px] flex-col bg-white shadow-2xl transition-transform duration-300 ease-out dark:bg-slate-900"
      :class="open ? 'translate-x-0' : 'pointer-events-none translate-x-full rtl:-translate-x-full'"
      :aria-hidden="!open"
      role="dialog"
      aria-modal="true"
    >
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4 dark:border-slate-800">
        <div class="flex items-center gap-2">
          <span v-if="items.length" class="grid h-8 w-8 place-items-center rounded-full bg-emerald-100 text-emerald-600">
            <Check class="h-5 w-5" />
          </span>
          <h2 class="font-heading text-lg font-bold text-ink">{{ items.length ? $t('flyout.addedTitle') : $t('flyout.cartTitle') }}</h2>
        </div>
        <button class="grid h-9 w-9 place-items-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-ink dark:hover:bg-slate-800" @click="close">
          <X class="h-5 w-5" />
        </button>
      </div>

      <!-- Empty -->
      <div v-if="!items.length" class="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
        <span class="grid h-16 w-16 place-items-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-slate-800"><ShoppingBag class="h-8 w-8" /></span>
        <div>
          <p class="font-semibold text-ink">{{ $t('flyout.empty') }}</p>
          <p class="mt-1 text-sm text-muted">{{ $t('flyout.emptyMsg') }}</p>
        </div>
        <button class="btn btn-primary btn-sm" @click="goShop">{{ $t('flyout.startShopping') }}</button>
      </div>

      <template v-else>
        <!-- Free shipping progress -->
        <div class="border-b border-slate-100 px-5 py-4 dark:border-slate-800">
          <p class="flex items-center gap-2 text-sm font-medium" :class="qualifies ? 'text-emerald-600' : 'text-ink'">
            <Truck class="h-4 w-4 shrink-0" />
            <span v-if="qualifies">{{ $t('flyout.freeShipDone') }}</span>
            <span v-else>{{ $t('flyout.freeShipRemain', { amount: `${remaining.toFixed(0)} ${currency}` }) }}</span>
          </p>
          <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
            <div class="h-full rounded-full bg-emerald-500 transition-all duration-500" :style="{ width: `${progress}%` }"></div>
          </div>
        </div>

        <!-- Items -->
        <div class="ewc-scroll flex-1 overflow-y-auto px-4 py-3">
          <div v-for="item in items" :key="item.id" class="flex gap-3 border-b border-slate-50 py-3 last:border-0 dark:border-slate-800/60">
            <component :is="pid(item) ? 'RouterLink' : 'div'" :to="pid(item) ? { name: 'product', params: { id: pid(item) } } : undefined" class="shrink-0" @click="pid(item) && close()">
              <img :src="productImage({ id: item.variant })" :alt="item.product_name" class="h-20 w-20 rounded-lg border border-slate-100 object-cover dark:border-slate-800" @error="onImgError" />
            </component>
            <div class="flex min-w-0 flex-1 flex-col">
              <div class="flex items-start justify-between gap-2">
                <component :is="pid(item) ? 'RouterLink' : 'span'" :to="pid(item) ? { name: 'product', params: { id: pid(item) } } : undefined" class="clamp-2 text-sm font-medium text-ink hover:text-primary-600" @click="pid(item) && close()">
                  {{ item.product_name }}
                </component>
                <button class="shrink-0 text-slate-300 hover:text-rose-600" :title="$t('flyout.remove')" @click="cart.removeItem(item.id)"><Trash2 class="h-4 w-4" /></button>
              </div>
              <div class="mt-auto flex items-end justify-between pt-2">
                <div class="inline-flex items-center rounded-lg border border-slate-200 dark:border-slate-700">
                  <button class="grid h-7 w-7 place-items-center text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800" @click="updateQty(item, item.quantity - 1)"><Minus class="h-3 w-3" /></button>
                  <span class="w-8 text-center text-sm font-semibold">{{ item.quantity }}</span>
                  <button class="grid h-7 w-7 place-items-center text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800" @click="updateQty(item, item.quantity + 1)"><Plus class="h-3 w-3" /></button>
                </div>
                <span class="text-sm font-bold text-ink">{{ item.line_total }} {{ currency }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="border-t border-slate-100 px-5 py-4 dark:border-slate-800">
          <div class="mb-3 flex items-center justify-between">
            <span class="text-sm text-muted">{{ $t('flyout.subtotal') }} · {{ data.item_count }} {{ data.item_count === 1 ? $t('flyout.item') : $t('flyout.items') }}</span>
            <span class="font-heading text-xl font-bold text-ink">{{ data.subtotal }} {{ currency }}</span>
          </div>
          <button class="btn btn-primary btn-lg w-full" @click="goCheckout">{{ $t('flyout.checkout') }} <ArrowRight class="h-4 w-4 rtl:rotate-180" /></button>
          <button class="btn btn-outline btn-sm mt-2 w-full" @click="goCart">{{ $t('flyout.viewCart') }}</button>
        </div>
      </template>
    </aside>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.ewc-scroll::-webkit-scrollbar {
  width: 8px;
}
.ewc-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
</style>
