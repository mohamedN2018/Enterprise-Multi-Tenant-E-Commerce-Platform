<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, Printer, Check, X, XCircle, Truck, Ticket, ShoppingBag, Send } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { pos } from '@/services/pos';
import { errorMessage } from '@/services/http';
import { useValidation, required } from '@/utils/validators';
import OrderTimeline from '@/components/OrderTimeline.vue';
import { NEXT_STATUS, statusLabel } from '@/utils/orderStatus';
import { t } from '@/i18n';

const route = useRoute();
const router = useRouter();
const tenant = useTenantStore();
const ui = useUiStore();

const order = ref(null);
const loading = ref(true);
const failed = ref(false);
const acting = ref(false);

const currency = computed(() => order.value?.currency || '');
const address = computed(() => (order.value?.shipping_address && typeof order.value.shipping_address === 'object' ? order.value.shipping_address : null));

// Cashier (POS) push — manual (re)send of a paid order to the linked cashier.
const hasCashier = ref(false);
const pushing = ref(false);
const isPaid = computed(() => order.value && !['pending', 'cancelled'].includes(order.value.status));
const pushToCashier = async () => {
  pushing.value = true;
  try {
    const res = await seller.pushOrderToCashier(order.value.id);
    order.value = res.data;
    // Trust the cashier's confirmation, not just a 2xx: the server only stamps
    // pos_synced_at when the cashier replied with a real order id.
    if (res.data?.pos_synced_at) {
      ui.success(t('orderDetailPage.posSent'));
    } else {
      ui.error(t('orderDetailPage.posNotConfirmed'));
    }
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    pushing.value = false;
  }
};

// Fulfillment status advance (processing → shipped → out for delivery → delivered)
const nextStatuses = computed(() => NEXT_STATUS[order.value?.status] || []);
const advTracking = ref('');
const advCarrier = ref('');
const advancing = ref(false);
const advance = async (status) => {
  advancing.value = true;
  try {
    const payload = { status };
    if (advTracking.value.trim()) payload.tracking_number = advTracking.value.trim();
    if (advCarrier.value.trim()) payload.carrier = advCarrier.value.trim();
    const res = await seller.updateOrderStatus(order.value.id, payload);
    order.value = res.data;
    ui.success(t('orderTrack.statusUpdated'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    advancing.value = false;
  }
};

const load = async () => {
  loading.value = true;
  failed.value = false;
  try {
    await tenant.ensureReady();
    const res = await seller.order(route.params.id);
    order.value = res.data;
    advTracking.value = order.value?.tracking_number || '';
    advCarrier.value = order.value?.carrier || '';
    try {
      const sup = await pos.supplier();
      hasCashier.value = !!sup?.data?.is_connected;
    } catch {
      hasCashier.value = false;
    }
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
};

const act = async (kind) => {
  acting.value = true;
  try {
    const res = kind === 'confirm' ? await seller.confirmOrder(order.value.id) : await seller.cancelOrder(order.value.id);
    order.value = res.data;
    ui.success(kind === 'confirm' ? t('orderDetailPage.confirmed') : t('orderDetailPage.cancelled'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    acting.value = false;
  }
};

const print = () => window.print();

// Tracking
const trackModal = ref(false);
const trackNumber = ref('');
const trackBusy = ref(false);
const { errors, run, clear } = useValidation(() => ({ trackNumber: trackNumber.value }), { trackNumber: [required()] });
const openTrack = () => {
  trackNumber.value = order.value?.tracking_number || '';
  trackModal.value = true;
};
const saveTracking = async () => {
  if (!run()) return;
  trackBusy.value = true;
  try {
    await seller.setOrderTracking(order.value.id, { tracking_number: trackNumber.value });
    order.value.tracking_number = trackNumber.value;
    ui.success(t('orderDetailPage.trackingAdded'));
    trackModal.value = false;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    trackBusy.value = false;
  }
};

onMounted(load);
</script>

<template>
  <div>
    <div v-if="loading" class="flex min-h-[50vh] items-center justify-center"><Spinner :size="30" :label="$t('orderDetailPage.loading')" /></div>

    <EmptyState v-else-if="failed || !order" :icon="ShoppingBag" :title="$t('orderDetailPage.notFound')" :message="$t('orderDetailPage.notFoundMsg')">
      <RouterLink :to="{ name: 'admin-orders' }" class="btn btn-primary btn-sm">{{ $t('orderDetailPage.backToOrders') }}</RouterLink>
    </EmptyState>

    <template v-else>
      <div class="no-print">
        <PageHeader :title="`${$t('orderDetailPage.title')} #${order.number}`" :subtitle="(order.placed_at || order.created_at || '').slice(0, 10)">
          <template #actions>
            <button class="btn btn-ghost btn-sm" @click="router.push({ name: 'admin-orders' })"><ArrowLeft class="h-4 w-4 rtl:rotate-180" /> {{ $t('orderDetailPage.back') }}</button>
            <button class="btn btn-outline btn-sm" @click="print"><Printer class="h-4 w-4" /> {{ $t('orderDetailPage.printInvoice') }}</button>
            <button v-if="tenant.canWrite" class="btn btn-outline btn-sm" @click="openTrack"><Truck class="h-4 w-4" /> {{ $t('orderDetailPage.trackingLabel') }}</button>
            <button v-if="tenant.canWrite && hasCashier && isPaid" class="btn btn-outline btn-sm" :disabled="pushing" @click="pushToCashier">
              <Send class="h-4 w-4" /> {{ order.pos_synced_at ? $t('orderDetailPage.posResend') : $t('orderDetailPage.posSend') }}
            </button>
            <template v-if="tenant.canWrite && order.status === 'pending'">
              <button class="btn btn-danger btn-sm" :disabled="acting" @click="act('cancel')"><X class="h-4 w-4" /> {{ $t('orderDetailPage.cancel') }}</button>
              <button class="btn btn-primary btn-sm" :disabled="acting" @click="act('confirm')"><Check class="h-4 w-4" /> {{ $t('orderDetailPage.confirm') }}</button>
            </template>
          </template>
        </PageHeader>
      </div>

      <!-- Cashier sync indicator (shown once the order reaches the cashier) -->
      <div v-if="order.pos_synced_at" class="no-print mb-4 flex flex-wrap items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10">
        <Check class="h-4 w-4 shrink-0" />
        <span class="font-medium">{{ $t('orderDetailPage.posSynced') }}</span>
        <span class="text-emerald-600/80">· {{ (order.pos_synced_at || '').replace('T', ' ').slice(0, 16) }}</span>
        <span v-if="order.pos_reference" class="text-emerald-600/70">· {{ order.pos_reference.slice(0, 8) }}</span>
      </div>

      <!-- Fulfillment tracking + status control -->
      <div class="no-print mb-6 grid gap-4 lg:grid-cols-2">
        <div class="card p-5">
          <h3 class="mb-4 flex items-center gap-2 font-semibold"><Truck class="h-5 w-5 text-primary-600" /> {{ $t('orderTrack.trackTitle') }}</h3>
          <OrderTimeline :order="order" />
        </div>
        <div v-if="tenant.canWrite && nextStatuses.length" class="card h-fit p-5">
          <h3 class="mb-3 font-semibold">{{ $t('orderTrack.updateTitle') }}</h3>
          <div class="grid gap-3 sm:grid-cols-2">
            <FormField v-model="advCarrier" :label="$t('orderTrack.carrier')" :placeholder="$t('orderTrack.carrierPlaceholder')" />
            <FormField v-model="advTracking" :label="$t('orderTrack.trackingNo')" :placeholder="$t('orderTrack.trackingPlaceholder')" />
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            <button v-for="s in nextStatuses" :key="s" class="btn btn-primary btn-sm" :disabled="advancing" @click="advance(s)">
              {{ $t('orderTrack.moveTo', { label: statusLabel(s) }) }}
            </button>
          </div>
        </div>
      </div>

      <!-- Buyer's note -->
      <div v-if="order.notes" class="no-print mb-6 card border-s-4 border-primary-500 p-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ $t('checkout.notes') }}</p>
        <p class="mt-1 text-sm text-ink">{{ order.notes }}</p>
      </div>

      <!-- Invoice (printable) -->
      <div class="print-area mx-auto max-w-3xl rounded-xl border border-slate-200 bg-white p-8">
        <div class="flex items-start justify-between border-b border-slate-100 pb-6">
          <div>
            <img src="/brand/qtech-logo.png" alt="q-shop" class="h-12 w-auto" />
            <p class="mt-1 text-sm text-muted">{{ tenant.active?.name }}</p>
          </div>
          <div class="text-end">
            <p class="font-heading text-lg font-bold">{{ $t('orderDetailPage.invoice') }}</p>
            <p class="text-sm text-muted">#{{ order.number }}</p>
            <p class="text-sm text-muted">{{ (order.placed_at || order.created_at || '').slice(0, 10) }}</p>
            <div class="mt-1 flex justify-end"><StatusBadge :status="order.status" /></div>
          </div>
        </div>

        <div v-if="address || order.shipping_method || order.tracking_number" class="grid gap-4 border-b border-slate-100 py-6 sm:grid-cols-2">
          <div v-if="address">
            <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{{ $t('orderDetailPage.shipTo') }}</p>
            <p class="font-medium">{{ address.full_name }}</p>
            <p class="text-sm text-muted">{{ address.line1 }}<span v-if="address.line2">, {{ address.line2 }}</span></p>
            <p class="text-sm text-muted">{{ address.city }}, {{ address.region }} {{ address.postal_code }}</p>
            <p class="text-sm text-muted">{{ address.country }} · {{ address.phone }}</p>
          </div>
          <div>
            <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{{ $t('orderDetailPage.shipping') }}</p>
            <p class="flex items-center gap-2 text-sm"><Truck class="h-4 w-4 text-primary-600" /> {{ order.shipping_method || $t('orderDetailPage.standard') }}</p>
            <p v-if="order.tracking_number" class="text-sm text-muted">{{ $t('orderDetailPage.trackingLabel') }}: {{ order.tracking_number }}</p>
            <p v-if="order.coupon_code" class="flex items-center gap-2 text-sm text-muted"><Ticket class="h-4 w-4" /> {{ order.coupon_code }}</p>
          </div>
        </div>

        <table class="mt-6 w-full text-sm">
          <thead>
            <tr class="border-b border-slate-200 text-start text-xs uppercase text-slate-400">
              <th class="py-2 text-start">{{ $t('orderDetailPage.item') }}</th>
              <th class="py-2 text-end">{{ $t('orderDetailPage.unit') }}</th>
              <th class="py-2 text-end">{{ $t('orderDetailPage.qty') }}</th>
              <th class="py-2 text-end">{{ $t('common.total') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in order.items" :key="it.id" class="border-b border-slate-50">
              <td class="py-3">
                <p class="font-medium text-ink">{{ it.product_name }}</p>
                <p class="text-xs text-slate-400">SKU {{ it.sku }}</p>
              </td>
              <td class="py-3 text-end">{{ it.unit_price }}</td>
              <td class="py-3 text-end">{{ it.quantity }}</td>
              <td class="py-3 text-end font-medium">{{ it.line_total }} {{ currency }}</td>
            </tr>
          </tbody>
        </table>

        <div class="ms-auto mt-6 w-full max-w-xs space-y-1.5 text-sm">
          <div class="flex justify-between"><span class="text-muted">{{ $t('common.subtotal') }}</span><span>{{ order.subtotal }} {{ currency }}</span></div>
          <div v-if="Number(order.discount_total) > 0" class="flex justify-between text-emerald-600"><span>{{ $t('common.discount') }}</span><span>−{{ order.discount_total }} {{ currency }}</span></div>
          <div v-if="Number(order.tax_total) > 0" class="flex justify-between"><span class="text-muted">{{ $t('orderDetailPage.tax') }}</span><span>{{ order.tax_total }} {{ currency }}</span></div>
          <div v-if="Number(order.shipping_total) > 0" class="flex justify-between"><span class="text-muted">{{ $t('orderDetailPage.shipping') }}</span><span>{{ order.shipping_total }} {{ currency }}</span></div>
          <div class="flex justify-between border-t border-slate-200 pt-2 font-heading text-base font-bold"><span>{{ $t('common.total') }}</span><span>{{ order.total }} {{ currency }}</span></div>
        </div>

        <p class="mt-8 border-t border-slate-100 pt-4 text-center text-xs text-slate-400">{{ $t('orderDetailPage.thankYou', { store: tenant.active?.name }) }}</p>
      </div>

      <Modal v-model="trackModal" :title="$t('orderDetailPage.setTracking')" size="sm">
        <FormField v-model="trackNumber" :label="$t('orderDetailPage.trackingNumber')" placeholder="e.g. 1Z999AA10123456784" required :error="errors.trackNumber" @update:model-value="clear('trackNumber')" />
        <template #footer>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="trackModal = false">{{ $t('common.cancel') }}</button>
            <button class="btn btn-primary" :disabled="trackBusy || !trackNumber" @click="saveTracking"><Spinner v-if="trackBusy" :size="18" /><span v-else>{{ $t('orderDetailPage.save') }}</span></button>
          </div>
        </template>
      </Modal>
    </template>
  </div>
</template>
