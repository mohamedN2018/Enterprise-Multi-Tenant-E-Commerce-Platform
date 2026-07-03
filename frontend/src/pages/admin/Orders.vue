<script setup>
import { ref, computed, onMounted } from 'vue';
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
import { t } from '@/i18n';

const router = useRouter();
const tenant = useTenantStore();

const statusFilter = ref('');
const columns = computed(() => [
  { key: 'number', label: t('ordersPage.order'), sortable: true },
  { key: 'created_at', label: t('common.date'), sortable: true },
  { key: 'items', label: t('ordersPage.items'), align: 'right' },
  { key: 'total', label: t('common.total'), align: 'right', sortable: true },
  { key: 'status', label: t('common.status'), sortable: true },
  { key: 'actions', label: '', align: 'right' }
]);

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
    <PageHeader :title="$t('ordersPage.title')" :subtitle="$t('ordersPage.subtitle')">
      <template #actions>
        <button class="btn btn-outline btn-sm" :disabled="!items.length" @click="exportCsv"><Download class="h-4 w-4" /> {{ $t('ordersPage.exportCsv') }}</button>
      </template>
    </PageHeader>

    <div class="mb-4">
      <select v-model="statusFilter" class="input max-w-[180px]" @change="applyFilter">
        <option value="">{{ $t('common.allStatuses') }}</option>
        <option value="pending">{{ $t('status.pending') }}</option>
        <option value="confirmed">{{ $t('status.confirmed') }}</option>
        <option value="cancelled">{{ $t('status.cancelled') }}</option>
      </select>
    </div>

    <DataTable :columns="columns" :rows="items" :loading="loading" clickable :empty-title="$t('ordersPage.noOrders')" :empty-message="$t('ordersPage.noOrdersMsg')" @row-click="openOrder">
      <template #cell-number="{ value }"><span class="font-medium text-ink">#{{ value }}</span></template>
      <template #cell-created_at="{ row }">{{ (row.placed_at || row.created_at || '').slice(0, 10) }}</template>
      <template #cell-items="{ row }">{{ row.items?.length || 0 }}</template>
      <template #cell-total="{ row }">{{ row.total }} {{ row.currency }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <button class="btn btn-ghost btn-sm" @click.stop="openOrder(row)"><Eye class="h-4 w-4" /> {{ $t('ordersPage.view') }}</button>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6">
      <Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" />
    </div>
  </div>
</template>
