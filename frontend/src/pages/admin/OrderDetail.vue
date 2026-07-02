<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, Printer, Check, X, Truck, Ticket, ShoppingBag } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';

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

const load = async () => {
  loading.value = true;
  failed.value = false;
  try {
    await tenant.ensureReady();
    const res = await seller.order(route.params.id);
    order.value = res.data;
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
    ui.success(kind === 'confirm' ? 'Order confirmed.' : 'Order cancelled.');
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
const openTrack = () => {
  trackNumber.value = order.value?.tracking_number || '';
  trackModal.value = true;
};
const saveTracking = async () => {
  trackBusy.value = true;
  try {
    await seller.setOrderTracking(order.value.id, { tracking_number: trackNumber.value });
    order.value.tracking_number = trackNumber.value;
    ui.success('Tracking number set.');
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
    <div v-if="loading" class="flex min-h-[50vh] items-center justify-center"><Spinner :size="30" label="Loading order…" /></div>

    <EmptyState v-else-if="failed || !order" :icon="ShoppingBag" title="Order not found" message="This order could not be loaded.">
      <RouterLink :to="{ name: 'admin-orders' }" class="btn btn-primary btn-sm">Back to orders</RouterLink>
    </EmptyState>

    <template v-else>
      <div class="no-print">
        <PageHeader :title="`Order #${order.number}`" :subtitle="(order.placed_at || order.created_at || '').slice(0, 10)">
          <template #actions>
            <button class="btn btn-ghost btn-sm" @click="router.push({ name: 'admin-orders' })"><ArrowLeft class="h-4 w-4" /> Back</button>
            <button class="btn btn-outline btn-sm" @click="print"><Printer class="h-4 w-4" /> Print invoice</button>
            <button v-if="tenant.canWrite" class="btn btn-outline btn-sm" @click="openTrack"><Truck class="h-4 w-4" /> Tracking</button>
            <template v-if="tenant.canWrite && order.status === 'pending'">
              <button class="btn btn-danger btn-sm" :disabled="acting" @click="act('cancel')"><X class="h-4 w-4" /> Cancel</button>
              <button class="btn btn-primary btn-sm" :disabled="acting" @click="act('confirm')"><Check class="h-4 w-4" /> Confirm</button>
            </template>
          </template>
        </PageHeader>
      </div>

      <!-- Invoice (printable) -->
      <div class="print-area mx-auto max-w-3xl rounded-xl border border-slate-200 bg-white p-8">
        <div class="flex items-start justify-between border-b border-slate-100 pb-6">
          <div>
            <img src="/brand/qtech-logo.png" alt="q-shop" class="h-12 w-auto" />
            <p class="mt-1 text-sm text-muted">{{ tenant.active?.name }}</p>
          </div>
          <div class="text-right">
            <p class="font-heading text-lg font-bold">INVOICE</p>
            <p class="text-sm text-muted">#{{ order.number }}</p>
            <p class="text-sm text-muted">{{ (order.placed_at || order.created_at || '').slice(0, 10) }}</p>
            <div class="mt-1 flex justify-end"><StatusBadge :status="order.status" /></div>
          </div>
        </div>

        <div v-if="address || order.shipping_method || order.tracking_number" class="grid gap-4 border-b border-slate-100 py-6 sm:grid-cols-2">
          <div v-if="address">
            <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">Ship to</p>
            <p class="font-medium">{{ address.full_name }}</p>
            <p class="text-sm text-muted">{{ address.line1 }}<span v-if="address.line2">, {{ address.line2 }}</span></p>
            <p class="text-sm text-muted">{{ address.city }}, {{ address.region }} {{ address.postal_code }}</p>
            <p class="text-sm text-muted">{{ address.country }} · {{ address.phone }}</p>
          </div>
          <div>
            <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">Shipping</p>
            <p class="flex items-center gap-2 text-sm"><Truck class="h-4 w-4 text-primary-600" /> {{ order.shipping_method || 'Standard' }}</p>
            <p v-if="order.tracking_number" class="text-sm text-muted">Tracking: {{ order.tracking_number }}</p>
            <p v-if="order.coupon_code" class="flex items-center gap-2 text-sm text-muted"><Ticket class="h-4 w-4" /> {{ order.coupon_code }}</p>
          </div>
        </div>

        <table class="mt-6 w-full text-sm">
          <thead>
            <tr class="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
              <th class="py-2">Item</th>
              <th class="py-2 text-right">Unit</th>
              <th class="py-2 text-right">Qty</th>
              <th class="py-2 text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in order.items" :key="it.id" class="border-b border-slate-50">
              <td class="py-3">
                <p class="font-medium text-ink">{{ it.product_name }}</p>
                <p class="text-xs text-slate-400">SKU {{ it.sku }}</p>
              </td>
              <td class="py-3 text-right">{{ it.unit_price }}</td>
              <td class="py-3 text-right">{{ it.quantity }}</td>
              <td class="py-3 text-right font-medium">{{ it.line_total }} {{ currency }}</td>
            </tr>
          </tbody>
        </table>

        <div class="ml-auto mt-6 w-full max-w-xs space-y-1.5 text-sm">
          <div class="flex justify-between"><span class="text-muted">Subtotal</span><span>{{ order.subtotal }} {{ currency }}</span></div>
          <div v-if="Number(order.discount_total) > 0" class="flex justify-between text-emerald-600"><span>Discount</span><span>−{{ order.discount_total }} {{ currency }}</span></div>
          <div v-if="Number(order.tax_total) > 0" class="flex justify-between"><span class="text-muted">Tax</span><span>{{ order.tax_total }} {{ currency }}</span></div>
          <div v-if="Number(order.shipping_total) > 0" class="flex justify-between"><span class="text-muted">Shipping</span><span>{{ order.shipping_total }} {{ currency }}</span></div>
          <div class="flex justify-between border-t border-slate-200 pt-2 font-heading text-base font-bold"><span>Total</span><span>{{ order.total }} {{ currency }}</span></div>
        </div>

        <p class="mt-8 border-t border-slate-100 pt-4 text-center text-xs text-slate-400">Thank you for shopping with {{ tenant.active?.name }} on q-shop.</p>
      </div>

      <Modal v-model="trackModal" title="Set tracking number" size="sm">
        <FormField v-model="trackNumber" label="Tracking number" placeholder="e.g. 1Z999AA10123456784" required />
        <template #footer>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="trackModal = false">Cancel</button>
            <button class="btn btn-primary" :disabled="trackBusy || !trackNumber" @click="saveTracking"><Spinner v-if="trackBusy" :size="18" /><span v-else>Save</span></button>
          </div>
        </template>
      </Modal>
    </template>
  </div>
</template>
