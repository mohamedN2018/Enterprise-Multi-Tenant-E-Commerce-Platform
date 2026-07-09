<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Plus, MapPin, Lock, Check, Truck, StickyNote, Navigation, AlertTriangle } from 'lucide-vue-next';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import PageHero from '@/components/ui/PageHero.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import DeliveryMap from '@/components/DeliveryMap.vue';
import { useCartStore } from '@/stores/cart';
import { useUiStore } from '@/stores/ui';
import { shop } from '@/services/shop';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, required, iso2 } from '@/utils/validators';
import { productImage, onImgError } from '@/utils/media';

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
const notes = ref('');
// Geo delivery: the store's delivery circles, the buyer's pinned location, and
// whether the store can deliver there.
const geoZones = ref([]);
const pinned = ref(null); // { lat, lng }
const deliverable = ref(true);
const hasGeoZones = computed(() => geoZones.value.length > 0);

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

// Server-computed preview so the summary shows the REAL total (tax + shipping
// included) — matching the order that gets placed. Falls back to the cart data.
const quote = ref(null);
const totals = computed(() => quote.value || data.value || {});
const refreshQuote = async () => {
  const chosen = addresses.value.find((a) => a.id === selectedAddress.value);
  try {
    const res = await shop.quote(cart.headers, {
      shipping_method_id: selectedMethod.value || undefined,
      address_id: selectedAddress.value || undefined,
      country: chosen?.country || cart.shopStore?.country || '',
      currency: cart.shopStore?.currency || '',
      lat: pinned.value?.lat,
      lng: pinned.value?.lng
    });
    quote.value = res.data;
    if (res.data?.deliverable != null) deliverable.value = res.data.deliverable;
  } catch {
    quote.value = null;
  }
};
// Re-quote whenever the shipping method, address, or pinned location changes.
watch([selectedMethod, selectedAddress], refreshQuote);
// A saved address may already carry a pin; adopt it so the map + zones match.
watch(selectedAddress, () => {
  const chosen = addresses.value.find((a) => a.id === selectedAddress.value);
  if (chosen?.lat != null && chosen?.lng != null) {
    pinned.value = { lat: Number(chosen.lat), lng: Number(chosen.lng) };
  }
});
// When the buyer moves the pin, refresh available methods + availability.
watch(pinned, async () => {
  await loadShipping();
  await refreshQuote();
});

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

const { errors, run, clear } = useValidation(
  () => form.value,
  {
    full_name: [required()],
    line1: [required()],
    city: [required()],
    postal_code: [required()],
    country: [iso2()]
  }
);

const saveAddress = async () => {
  if (!run()) return;
  savingAddress.value = true;
  try {
    // Remember the pinned map location on the address, if one was chosen.
    const payload = { ...form.value };
    if (pinned.value) {
      payload.lat = Number(pinned.value.lat.toFixed(6));
      payload.lng = Number(pinned.value.lng.toFixed(6));
    }
    const res = await shop.createAddress(cart.headers, payload);
    const created = res.data;
    addresses.value.push(created);
    selectedAddress.value = created.id;
    showForm.value = false;
    form.value = blankAddress();
    ui.success(t('checkout.addressSaved'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    savingAddress.value = false;
  }
};

const loadShipping = async () => {
  try {
    const res = await shop.availableShipping(cart.headers, {
      country: cart.shopStore?.country || '',
      lat: pinned.value?.lat,
      lng: pinned.value?.lng
    });
    const body = res.data || {};
    // New shape: { deliverable, methods, geo_zones }. Tolerate an old list too.
    shippingMethods.value = Array.isArray(body) ? body : body.methods || [];
    geoZones.value = body.geo_zones || [];
    if (body.deliverable != null) deliverable.value = body.deliverable;
    // Keep the selected method valid for the current location.
    if (!shippingMethods.value.some((m) => m.id === selectedMethod.value)) {
      selectedMethod.value = shippingMethods.value[0]?.id || null;
    }
  } catch {
    shippingMethods.value = [];
  }
};

const useMyLocation = () => {
  if (!navigator.geolocation) return ui.error(t('shippingPage.geoUnsupported'));
  navigator.geolocation.getCurrentPosition(
    (pos) => (pinned.value = { lat: pos.coords.latitude, lng: pos.coords.longitude }),
    () => ui.error(t('shippingPage.geoDenied'))
  );
};

const placeOrder = async () => {
  placing.value = true;
  try {
    const chosen = addresses.value.find((a) => a.id === selectedAddress.value);
    const order = await cart.checkout({
      address_id: selectedAddress.value || undefined,
      shipping_method_id: selectedMethod.value || undefined,
      country: chosen?.country || cart.shopStore?.country || '',
      currency: cart.shopStore?.currency || '',
      notes: notes.value.trim() || undefined,
      lat: pinned.value?.lat,
      lng: pinned.value?.lng
    });
    // Confirm immediately so the order is accepted (stock committed) and, when the
    // store is linked to a cashier, pushed there automatically so staff are alerted.
    // Best-effort: if it can't confirm (e.g. a fraud hold), the order still stands
    // and the seller can confirm it from the dashboard.
    try {
      await shop.confirmOrder(cart.headers, order.id);
    } catch {
      /* order placed; confirmation/push will be done from the dashboard */
    }
    ui.success(t('checkout.orderPlaced'));
    router.push({ name: 'order-confirmation', params: { id: order.id } });
  } catch (e) {
    const code = e?.response?.data?.error_code;
    // Cashier ran out of stock between browsing and paying → tell the buyer clearly.
    if (code === 'out_of_stock') {
      const items = e.response.data.errors?.out_of_stock || [];
      ui.error(t('checkout.outOfStock', { items: items.join('، ') }));
    } else if (code === 'delivery_unavailable') {
      deliverable.value = false;
      ui.error(t('checkout.deliveryUnavailable'));
    } else if (code === 'store_unavailable') {
      ui.error(t('checkout.storeUnavailable'));
    } else {
      ui.error(errorMessage(e));
    }
  } finally {
    placing.value = false;
  }
};

onMounted(async () => {
  await cart.refreshCart();
  await Promise.all([loadAddresses(), loadShipping()]);
  await refreshQuote();
  loading.value = false;
});
</script>

<template>
  <div>
    <PageHero :title="$t('checkout.title')" :items="[{ label: $t('cart.title'), to: { name: 'cart' } }, { label: $t('checkout.title') }]" />
    <div class="container py-10">

    <div v-if="loading" class="flex min-h-[30vh] items-center justify-center">
      <Spinner :size="28" :label="$t('checkout.preparing')" />
    </div>

    <EmptyState
      v-else-if="!items.length"
      :title="$t('checkout.emptyCart')"
      :message="$t('checkout.emptyCartMsg')"
    >
      <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-sm">{{ $t('checkout.browseProducts') }}</RouterLink>
    </EmptyState>

    <div v-else class="grid gap-8 lg:grid-cols-[1fr_360px]">
      <!-- Left: shipping -->
      <div class="space-y-6">
        <section class="card p-6">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="flex items-center gap-2 font-semibold"><MapPin class="h-5 w-5 text-primary-600" /> {{ $t('checkout.shippingAddress') }}</h2>
            <button v-if="addresses.length" class="btn btn-ghost btn-sm" @click="showForm = !showForm">
              <Plus class="h-4 w-4" /> {{ $t('checkout.newAddress') }}
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

          <form v-if="showForm" class="mt-4 grid gap-4 border-t border-slate-100 pt-4 sm:grid-cols-2" novalidate @submit.prevent="saveAddress">
            <FormField v-model="form.full_name" :label="$t('checkout.fullName')" :error="errors.full_name" class="sm:col-span-2" @update:model-value="clear('full_name')" />
            <FormField v-model="form.line1" :label="$t('checkout.line1')" :error="errors.line1" class="sm:col-span-2" @update:model-value="clear('line1')" />
            <FormField v-model="form.line2" :label="$t('checkout.line2')" />
            <FormField v-model="form.city" :label="$t('common.city')" :error="errors.city" @update:model-value="clear('city')" />
            <FormField v-model="form.region" :label="$t('checkout.region')" />
            <FormField v-model="form.postal_code" :label="$t('checkout.postal')" :error="errors.postal_code" @update:model-value="clear('postal_code')" />
            <FormField v-model="form.country" :label="$t('common.country')" maxlength="2" placeholder="US" :error="errors.country" @update:model-value="clear('country')" />
            <FormField v-model="form.phone" :label="$t('common.phone')" />
            <div class="sm:col-span-2">
              <button type="submit" class="btn btn-primary btn-sm" :disabled="savingAddress">
                <Spinner v-if="savingAddress" :size="16" /><span v-else>{{ $t('checkout.saveAddress') }}</span>
              </button>
            </div>
          </form>
        </section>

        <!-- Delivery location (only when the store delivers by map zones) -->
        <section v-if="hasGeoZones" class="card p-6">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="flex items-center gap-2 font-semibold"><Navigation class="h-5 w-5 text-primary-600" /> {{ $t('checkout.deliveryLocation') }}</h2>
            <button class="btn btn-ghost btn-sm" @click="useMyLocation"><MapPin class="h-4 w-4" /> {{ $t('shippingPage.useMyLocation') }}</button>
          </div>
          <p class="mb-3 text-sm text-muted">{{ pinned ? $t('checkout.locationSet') : $t('checkout.pickLocation') }}</p>
          <DeliveryMap v-model="pinned" editable :circles="geoZones" height="280px" />
          <div v-if="pinned && !deliverable" class="mt-3 flex items-start gap-2 rounded-lg border border-secondary-200 bg-secondary-50 p-3 text-sm text-secondary-700 dark:border-secondary-500/30 dark:bg-secondary-500/10">
            <AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" />
            <span>{{ $t('checkout.deliveryUnavailable') }}</span>
          </div>
          <div v-else-if="pinned && deliverable" class="mt-3 flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10">
            <Check class="h-4 w-4 shrink-0" /> {{ $t('checkout.deliveryAvailable') }}
          </div>
        </section>

        <!-- Shipping method -->
        <section v-if="shippingMethods.length" class="card p-6">
          <h2 class="mb-4 flex items-center gap-2 font-semibold"><Truck class="h-5 w-5 text-primary-600" /> {{ $t('checkout.shippingMethod') }}</h2>
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
              <span class="text-sm font-semibold">{{ Number(m.price) > 0 ? `${m.price} ${currency}` : $t('checkout.free') }}</span>
            </label>
          </div>
        </section>

        <!-- Order notes -->
        <section class="card p-6">
          <h2 class="mb-3 flex items-center gap-2 font-semibold"><StickyNote class="h-5 w-5 text-primary-600" /> {{ $t('checkout.notes') }}</h2>
          <textarea v-model="notes" rows="2" class="input" maxlength="500" :placeholder="$t('checkout.notesPlaceholder')"></textarea>
        </section>
      </div>

      <!-- Right: summary -->
      <aside class="h-fit space-y-4 lg:sticky lg:top-24">
        <div class="card p-5">
          <h3 class="font-semibold">{{ $t('checkout.orderSummary') }}</h3>
          <ul class="mt-4 space-y-3 border-b border-slate-100 pb-4">
            <li v-for="item in items" :key="item.id" class="flex items-center gap-2 text-sm">
              <img :src="item.product_image || productImage(item)" :alt="item.product_name" class="h-10 w-10 shrink-0 rounded-lg border border-slate-100 object-cover" @error="onImgError" />
              <span class="flex-1 text-slate-600">{{ item.product_name }} <span class="text-slate-400">× {{ item.quantity }}</span></span>
              <span class="font-medium">{{ item.line_total }} {{ currency }}</span>
            </li>
          </ul>
          <dl class="mt-4 space-y-2 text-sm">
            <div class="flex justify-between"><dt class="text-slate-500">{{ $t('common.subtotal') }}</dt><dd class="font-medium">{{ totals.subtotal }} {{ currency }}</dd></div>
            <div v-if="Number(totals.discount) > 0" class="flex justify-between text-emerald-600"><dt>{{ $t('common.discount') }}</dt><dd>−{{ totals.discount }} {{ currency }}</dd></div>
            <div v-if="quote && Number(quote.tax) > 0" class="flex justify-between"><dt class="text-slate-500">{{ $t('orderDetailPage.tax') }}</dt><dd>{{ quote.tax }} {{ currency }}</dd></div>
            <div v-if="quote" class="flex justify-between"><dt class="text-slate-500">{{ $t('orderDetailPage.shipping') }}</dt><dd>{{ Number(quote.shipping) > 0 ? `${quote.shipping} ${currency}` : $t('checkout.free') }}</dd></div>
            <div class="flex justify-between border-t border-slate-100 pt-2 text-base font-bold"><dt>{{ $t('common.total') }}</dt><dd>{{ totals.total }} {{ currency }}</dd></div>
          </dl>
          <button class="btn btn-primary btn-lg mt-5 w-full" :disabled="placing || (hasGeoZones && !deliverable)" @click="placeOrder">
            <Spinner v-if="placing" :size="18" />
            <template v-else><Lock class="h-4 w-4" /> {{ $t('checkout.placeOrder') }}</template>
          </button>
          <p v-if="hasGeoZones && !deliverable" class="mt-2 text-center text-xs text-secondary-600">{{ $t('checkout.deliveryUnavailableShort') }}</p>
          <p class="mt-3 flex items-center justify-center gap-1 text-xs text-slate-400">
            <Check class="h-3.5 w-3.5" /> {{ $t('checkout.secureCheckout') }}
          </p>
        </div>
      </aside>
    </div>
    </div>
  </div>
</template>
