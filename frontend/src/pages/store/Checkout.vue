<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Plus, MapPin, Lock, Check, Truck } from 'lucide-vue-next';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import PageHero from '@/components/ui/PageHero.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useCartStore } from '@/stores/cart';
import { useUiStore } from '@/stores/ui';
import { shop } from '@/services/shop';
import { errorMessage } from '@/services/http';

const router = useRouter();
const cart = useCartStore();
const ui = useUiStore();

const loading = ref(true);
const placing = ref(false);
const addresses = ref([]);
const selectedAddress = ref(null);
const showForm = ref(false);
const savingAddress = ref(false);
const shippingMethods = ref([]);
const selectedMethod = ref(null);

const blankAddress = () => ({
  label: 'Home',
  full_name: '',
  line1: '',
  line2: '',
  city: '',
  region: '',
  postal_code: '',
  country: cart.shopStore?.country || '',
  phone: '',
  is_default: true
});
const form = ref(blankAddress());

const currency = computed(() => cart.shopStore?.currency || '');
const data = computed(() => cart.cart);
const items = computed(() => data.value?.items || []);

const loadAddresses = async () => {
  try {
    const res = await shop.addresses(cart.headers);
    addresses.value = res.data?.results || res.data || [];
    const def = addresses.value.find((a) => a.is_default) || addresses.value[0];
    selectedAddress.value = def?.id || null;
    showForm.value = addresses.value.length === 0;
  } catch {
    addresses.value = [];
    showForm.value = true;
  }
};

const saveAddress = async () => {
  savingAddress.value = true;
  try {
    const res = await shop.createAddress(cart.headers, form.value);
    const created = res.data;
    addresses.value.push(created);
    selectedAddress.value = created.id;
    showForm.value = false;
    form.value = blankAddress();
    ui.success('Address saved.');
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    savingAddress.value = false;
  }
};

const loadShipping = async () => {
  try {
    const res = await shop.availableShipping(cart.headers);
    shippingMethods.value = res.data || [];
    if (shippingMethods.value.length) selectedMethod.value = shippingMethods.value[0].id;
  } catch {
    shippingMethods.value = [];
  }
};

const placeOrder = async () => {
  placing.value = true;
  try {
    const chosen = addresses.value.find((a) => a.id === selectedAddress.value);
    const order = await cart.checkout({
      address_id: selectedAddress.value || undefined,
      shipping_method_id: selectedMethod.value || undefined,
      country: chosen?.country || cart.shopStore?.country || '',
      currency: cart.shopStore?.currency || ''
    });
    ui.success('Order placed successfully!');
    router.push({ name: 'order-confirmation', params: { id: order.id } });
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    placing.value = false;
  }
};

onMounted(async () => {
  await cart.refreshCart();
  await Promise.all([loadAddresses(), loadShipping()]);
  loading.value = false;
});
</script>

<template>
  <div>
    <PageHero title="Checkout" :items="[{ label: 'Cart', to: { name: 'cart' } }, { label: 'Checkout' }]" />
    <div class="container py-10">

    <div v-if="loading" class="flex min-h-[30vh] items-center justify-center">
      <Spinner :size="28" label="Preparing checkout…" />
    </div>

    <EmptyState
      v-else-if="!items.length"
      title="Your cart is empty"
      message="Add items to your cart before checking out."
    >
      <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-sm">Browse products</RouterLink>
    </EmptyState>

    <div v-else class="grid gap-8 lg:grid-cols-[1fr_360px]">
      <!-- Left: shipping -->
      <div class="space-y-6">
        <section class="card p-6">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="flex items-center gap-2 font-semibold"><MapPin class="h-5 w-5 text-primary-600" /> Shipping address</h2>
            <button v-if="addresses.length" class="btn btn-ghost btn-sm" @click="showForm = !showForm">
              <Plus class="h-4 w-4" /> New address
            </button>
          </div>

          <div v-if="addresses.length" class="grid gap-3 sm:grid-cols-2">
            <label
              v-for="a in addresses"
              :key="a.id"
              class="flex cursor-pointer gap-3 rounded-lg border p-3 transition"
              :class="selectedAddress === a.id ? 'border-primary-500 bg-primary-50/50' : 'border-slate-200 hover:border-slate-300'"
            >
              <input v-model="selectedAddress" type="radio" :value="a.id" class="mt-1 text-primary-600 focus:ring-primary-500" />
              <div class="text-sm">
                <p class="font-semibold">{{ a.full_name }} <span class="text-xs font-normal text-slate-400">· {{ a.label }}</span></p>
                <p class="text-slate-500">{{ a.line1 }}<span v-if="a.line2">, {{ a.line2 }}</span></p>
                <p class="text-slate-500">{{ a.city }}, {{ a.region }} {{ a.postal_code }}</p>
                <p class="text-slate-500">{{ a.country }} · {{ a.phone }}</p>
              </div>
            </label>
          </div>

          <form v-if="showForm" class="mt-4 grid gap-4 border-t border-slate-100 pt-4 sm:grid-cols-2" @submit.prevent="saveAddress">
            <FormField v-model="form.full_name" label="Full name" required class="sm:col-span-2" />
            <FormField v-model="form.line1" label="Address line 1" required class="sm:col-span-2" />
            <FormField v-model="form.line2" label="Address line 2" />
            <FormField v-model="form.city" label="City" required />
            <FormField v-model="form.region" label="State / Region" />
            <FormField v-model="form.postal_code" label="Postal code" required />
            <FormField v-model="form.country" label="Country (ISO-2)" maxlength="2" placeholder="US" required />
            <FormField v-model="form.phone" label="Phone" />
            <div class="sm:col-span-2">
              <button type="submit" class="btn btn-primary btn-sm" :disabled="savingAddress">
                <Spinner v-if="savingAddress" :size="16" /><span v-else>Save address</span>
              </button>
            </div>
          </form>
        </section>

        <!-- Shipping method -->
        <section v-if="shippingMethods.length" class="card p-6">
          <h2 class="mb-4 flex items-center gap-2 font-semibold"><Truck class="h-5 w-5 text-primary-600" /> Shipping method</h2>
          <div class="grid gap-3">
            <label
              v-for="m in shippingMethods"
              :key="m.id"
              class="flex cursor-pointer items-center justify-between gap-3 rounded-lg border p-3 transition"
              :class="selectedMethod === m.id ? 'border-primary-500 bg-primary-50/50' : 'border-slate-200 hover:border-slate-300'"
            >
              <span class="flex items-center gap-3">
                <input v-model="selectedMethod" type="radio" :value="m.id" class="text-primary-600 focus:ring-primary-500" />
                <span>
                  <span class="block text-sm font-semibold">{{ m.name }}</span>
                  <span class="block text-xs text-muted">{{ m.zone_name }}</span>
                </span>
              </span>
              <span class="text-sm font-semibold">{{ Number(m.price) > 0 ? `${m.price} ${currency}` : 'Free' }}</span>
            </label>
          </div>
        </section>
      </div>

      <!-- Right: summary -->
      <aside class="h-fit space-y-4 lg:sticky lg:top-24">
        <div class="card p-5">
          <h3 class="font-semibold">Order summary</h3>
          <ul class="mt-4 space-y-3 border-b border-slate-100 pb-4">
            <li v-for="item in items" :key="item.id" class="flex justify-between gap-2 text-sm">
              <span class="text-slate-600">{{ item.product_name }} <span class="text-slate-400">× {{ item.quantity }}</span></span>
              <span class="font-medium">{{ item.line_total }} {{ currency }}</span>
            </li>
          </ul>
          <dl class="mt-4 space-y-2 text-sm">
            <div class="flex justify-between"><dt class="text-slate-500">Subtotal</dt><dd class="font-medium">{{ data.subtotal }} {{ currency }}</dd></div>
            <div v-if="Number(data.discount) > 0" class="flex justify-between text-emerald-600"><dt>Discount</dt><dd>−{{ data.discount }} {{ currency }}</dd></div>
            <div class="flex justify-between border-t border-slate-100 pt-2 text-base font-bold"><dt>Total</dt><dd>{{ data.total }} {{ currency }}</dd></div>
          </dl>
          <button class="btn btn-primary btn-lg mt-5 w-full" :disabled="placing" @click="placeOrder">
            <Spinner v-if="placing" :size="18" />
            <template v-else><Lock class="h-4 w-4" /> Place order</template>
          </button>
          <p class="mt-3 flex items-center justify-center gap-1 text-xs text-slate-400">
            <Check class="h-3.5 w-3.5" /> Secure, encrypted checkout
          </p>
        </div>
      </aside>
    </div>
    </div>
  </div>
</template>
