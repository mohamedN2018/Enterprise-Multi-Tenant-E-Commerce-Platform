<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Eye, Download } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import DataTable from '@/components/ui/DataTable.vue';
import Pagination from '@/components/ui/Pagination.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import { useTenantStore } from '@/stores/tenant';
import { usePaginated } from '@/composables/usePaginated';
import { seller } from '@/services/seller';
import { downloadCsv } from '@/utils/csv';

const router = useRouter();
const tenant = useTenantStore();

const statusFilter = ref('');
const columns = [
  { key: 'number', label: 'Order', sortable: true },
  { key: 'created_at', label: 'Date', sortable: true },
  { key: 'items', label: 'Items', align: 'right' },
  { key: 'total', label: 'Total', align: 'right', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
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

const openOrder = (o) => router.push({ name: 'admin-order-detail', params: { id: o.id } });

const exportCsv = () => {
  const rows = items.value.map((o) => ({
    number: o.number,
    date: (o.placed_at || o.created_at || '').slice(0, 10),
    status: o.status,
    items: o.items?.length || 0,
    total: o.total,
    currency: o.currency
  }));
  downloadCsv(`orders-${new Date().toISOString().slice(0, 10)}.csv`, rows);
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) fetch();
});
</script>

<template>
  <div>
    <PageHeader title="Orders" subtitle="Track and fulfil customer orders.">
      <template #actions>
        <button class="btn btn-outline btn-sm" :disabled="!items.length" @click="exportCsv"><Download class="h-4 w-4" /> Export CSV</button>
      </template>
    </PageHeader>

    <div class="mb-4">
      <select v-model="statusFilter" class="input max-w-[180px]" @change="applyFilter">
        <option value="">All statuses</option>
        <option value="pending">Pending</option>
        <option value="confirmed">Confirmed</option>
        <option value="cancelled">Cancelled</option>
      </select>
    </div>

    <DataTable :columns="columns" :rows="items" :loading="loading" clickable empty-title="No orders yet" empty-message="Orders placed by customers will appear here." @row-click="openOrder">
      <template #cell-number="{ value }"><span class="font-medium text-ink">#{{ value }}</span></template>
      <template #cell-created_at="{ row }">{{ (row.placed_at || row.created_at || '').slice(0, 10) }}</template>
      <template #cell-items="{ row }">{{ row.items?.length || 0 }}</template>
      <template #cell-total="{ row }">{{ row.total }} {{ row.currency }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <button class="btn btn-ghost btn-sm" @click.stop="openOrder(row)"><Eye class="h-4 w-4" /> View</button>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6">
      <Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" />
    </div>
  </div>
</template>
