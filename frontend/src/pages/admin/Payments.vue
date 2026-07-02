<script setup>
import { ref, onMounted } from 'vue';
import { CreditCard, CheckCheck } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import DataTable from '@/components/ui/DataTable.vue';
import Pagination from '@/components/ui/Pagination.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { usePaginated } from '@/composables/usePaginated';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';

const tenant = useTenantStore();
const ui = useUiStore();

const gateways = ref([]);
const acting = ref(null);

const columns = [
  { key: 'created_at', label: 'Date', sortable: true },
  { key: 'order', label: 'Order' },
  { key: 'gateway', label: 'Gateway', sortable: true },
  { key: 'amount', label: 'Amount', align: 'right', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'actions', label: '', align: 'right' }
];

const { items, page, total, totalPages, loading, load } = usePaginated((params) => seller.paymentsManage(params));
const changePage = (n) => {
  page.value = n;
  load();
};

const capture = async (p) => {
  acting.value = p.id;
  try {
    await seller.capturePayment(p.id);
    ui.success('Payment captured.');
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    acting.value = null;
  }
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (!id) return;
  try {
    const g = await seller.gateways();
    gateways.value = g.data || [];
  } catch {
    gateways.value = [];
  }
  load();
});
</script>

<template>
  <div>
    <PageHeader title="Payments" subtitle="Payment transactions across your store." />

    <div v-if="gateways.length" class="mb-4 flex flex-wrap gap-2">
      <span v-for="g in gateways" :key="g.code" class="chip border-slate-200 bg-white text-ink"><CreditCard class="h-3.5 w-3.5 text-primary-600" /> {{ g.display_name || g.code }}</span>
    </div>

    <DataTable :columns="columns" :rows="items" :loading="loading" empty-title="No payments" empty-message="Payments for your orders will appear here.">
      <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
      <template #cell-order="{ value }"><span class="font-mono text-xs">{{ String(value).slice(0, 8) }}</span></template>
      <template #cell-gateway="{ value }"><span class="capitalize">{{ value }}</span></template>
      <template #cell-amount="{ row }">{{ row.amount }} {{ row.currency }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <button v-if="tenant.canWrite && ['pending', 'authorized', 'requires_capture'].includes(row.status)" class="btn btn-ghost btn-sm text-emerald-600" :disabled="acting === row.id" @click="capture(row)">
          <CheckCheck class="h-4 w-4" /> Capture
        </button>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6"><Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" /></div>
  </div>
</template>
