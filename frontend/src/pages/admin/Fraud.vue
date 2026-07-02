<script setup>
import { ref, onMounted } from 'vue';
import { ShieldCheck, ShieldX, ShieldAlert } from 'lucide-vue-next';
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
const acting = ref(null);

const columns = [
  { key: 'created_at', label: 'Date', sortable: true },
  { key: 'order_number', label: 'Order', sortable: true },
  { key: 'order_total', label: 'Total', align: 'right', sortable: true },
  { key: 'score', label: 'Risk score', align: 'right', sortable: true },
  { key: 'decision', label: 'Decision', sortable: true },
  { key: 'reasons', label: 'Reasons' },
  { key: 'resolution', label: 'Resolution', sortable: true },
  { key: 'actions', label: '', align: 'right' }
];

const { items, page, total, totalPages, loading, load } = usePaginated((params) => seller.fraudChecks(params));
const changePage = (n) => {
  page.value = n;
  load();
};

const run = async (row, fn, msg) => {
  acting.value = row.id;
  try {
    await fn();
    ui.success(msg);
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    acting.value = null;
  }
};
const clear = (row) => run(row, () => seller.clearFraud(row.id), 'Marked as cleared.');
const reject = (row) => run(row, () => seller.rejectFraud(row.id), 'Flagged as fraud.');

const scoreTone = (s) => (Number(s) >= 70 ? 'text-secondary-500' : Number(s) >= 40 ? 'text-amber-600' : 'text-emerald-600');

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) load();
});
</script>

<template>
  <div>
    <PageHeader title="Fraud review" subtitle="Risk checks on orders flagged for review.">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">Read-only</span>
      </template>
    </PageHeader>

    <DataTable :columns="columns" :rows="items" :loading="loading" empty-title="No fraud checks" empty-message="Orders flagged for review will appear here.">
      <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
      <template #cell-order_number="{ value }"><span class="font-medium text-ink">#{{ value }}</span></template>
      <template #cell-order_total="{ row }">{{ row.order_total }} {{ tenant.currency }}</template>
      <template #cell-score="{ value }"><span class="font-semibold" :class="scoreTone(value)">{{ value }}</span></template>
      <template #cell-decision="{ value }"><span class="capitalize">{{ value }}</span></template>
      <template #cell-reasons="{ value }"><span class="clamp-1 block max-w-xs text-xs text-muted">{{ Array.isArray(value) ? value.join(', ') : value || '—' }}</span></template>
      <template #cell-resolution="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <div v-if="tenant.canWrite && (row.resolution === 'pending' || !row.resolution)" class="flex justify-end gap-1">
          <button class="btn btn-ghost btn-sm text-emerald-600" :disabled="acting === row.id" @click="clear(row)"><ShieldCheck class="h-4 w-4" /> Clear</button>
          <button class="btn btn-ghost btn-sm text-secondary-500" :disabled="acting === row.id" @click="reject(row)"><ShieldX class="h-4 w-4" /> Reject</button>
        </div>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6"><Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" /></div>
  </div>
</template>
