<script setup>
import { ref, onMounted } from 'vue';
import { Eye, Check, X } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import DataTable from '@/components/ui/DataTable.vue';
import Pagination from '@/components/ui/Pagination.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Modal from '@/components/ui/Modal.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { usePaginated } from '@/composables/usePaginated';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';

const tenant = useTenantStore();
const ui = useUiStore();

const statusFilter = ref('');
const columns = [
  { key: 'number', label: 'Order' },
  { key: 'created_at', label: 'Date' },
  { key: 'items', label: 'Items', align: 'right' },
  { key: 'total', label: 'Total', align: 'right' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '', align: 'right' }
];

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  seller.orders(params)
);
const fetch = () => load(statusFilter.value ? { status: statusFilter.value } : {});
const changePage = (n) => {
  page.value = n;
  fetch();
};
const applyFilter = () => {
  page.value = 1;
  fetch();
};

const selected = ref(null);
const acting = ref(false);

const confirmOrder = async (o) => {
  acting.value = true;
  try {
    const res = await seller.confirmOrder(o.id);
    ui.success('Order confirmed.');
    if (selected.value) selected.value = res.data;
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    acting.value = false;
  }
};
const cancelOrder = async (o) => {
  acting.value = true;
  try {
    const res = await seller.cancelOrder(o.id);
    ui.success('Order cancelled.');
    if (selected.value) selected.value = res.data;
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    acting.value = false;
  }
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) fetch();
});
</script>

<template>
  <div>
    <PageHeader title="Orders" subtitle="Track and fulfil customer orders." />

    <div class="mb-4">
      <select v-model="statusFilter" class="input max-w-[180px]" @change="applyFilter">
        <option value="">All statuses</option>
        <option value="pending">Pending</option>
        <option value="confirmed">Confirmed</option>
        <option value="cancelled">Cancelled</option>
      </select>
    </div>

    <DataTable :columns="columns" :rows="items" :loading="loading" clickable empty-title="No orders yet" empty-message="Orders placed by customers will appear here." @row-click="selected = $event">
      <template #cell-number="{ value }"><span class="font-medium text-ink">#{{ value }}</span></template>
      <template #cell-created_at="{ row }">{{ (row.placed_at || row.created_at || '').slice(0, 10) }}</template>
      <template #cell-items="{ row }">{{ row.items?.length || 0 }}</template>
      <template #cell-total="{ row }">{{ row.total }} {{ row.currency }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <button class="btn btn-ghost btn-sm" @click.stop="selected = row"><Eye class="h-4 w-4" /></button>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6">
      <Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" />
    </div>

    <!-- Order detail -->
    <Modal :model-value="!!selected" :title="selected ? `Order #${selected.number}` : ''" size="lg" @update:model-value="selected = null">
      <template v-if="selected">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <StatusBadge :status="selected.status" />
          <span class="text-sm text-slate-500">{{ (selected.placed_at || selected.created_at || '').slice(0, 10) }}</span>
        </div>

        <ul class="mt-4 divide-y divide-slate-100 border-y border-slate-100">
          <li v-for="it in selected.items" :key="it.id" class="flex items-center justify-between py-3 text-sm">
            <div>
              <p class="font-medium">{{ it.product_name }}</p>
              <p class="text-xs text-slate-400">SKU {{ it.sku }} · {{ it.unit_price }} × {{ it.quantity }}</p>
            </div>
            <span class="font-semibold">{{ it.line_total }} {{ selected.currency }}</span>
          </li>
        </ul>

        <dl class="mt-4 space-y-1.5 text-sm">
          <div class="flex justify-between"><dt class="text-slate-500">Subtotal</dt><dd>{{ selected.subtotal }} {{ selected.currency }}</dd></div>
          <div v-if="Number(selected.discount_total) > 0" class="flex justify-between text-emerald-600"><dt>Discount</dt><dd>−{{ selected.discount_total }} {{ selected.currency }}</dd></div>
          <div v-if="Number(selected.tax_total) > 0" class="flex justify-between"><dt class="text-slate-500">Tax</dt><dd>{{ selected.tax_total }} {{ selected.currency }}</dd></div>
          <div v-if="Number(selected.shipping_total) > 0" class="flex justify-between"><dt class="text-slate-500">Shipping</dt><dd>{{ selected.shipping_total }} {{ selected.currency }}</dd></div>
          <div class="flex justify-between border-t border-slate-100 pt-2 text-base font-bold"><dt>Total</dt><dd>{{ selected.total }} {{ selected.currency }}</dd></div>
        </dl>
      </template>

      <template #footer>
        <div class="flex justify-end gap-2">
          <button v-if="tenant.canWrite && selected && selected.status === 'pending'" class="btn btn-danger" :disabled="acting" @click="cancelOrder(selected)">
            <X class="h-4 w-4" /> Cancel
          </button>
          <button v-if="tenant.canWrite && selected && selected.status === 'pending'" class="btn btn-primary" :disabled="acting" @click="confirmOrder(selected)">
            <Spinner v-if="acting" :size="18" /><template v-else><Check class="h-4 w-4" /> Confirm</template>
          </button>
          <button class="btn btn-ghost" @click="selected = null">Close</button>
        </div>
      </template>
    </Modal>
  </div>
</template>
