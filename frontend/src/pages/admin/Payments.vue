<script setup>
import { ref, computed, onMounted } from 'vue';
import { CreditCard, CheckCheck, Download } from 'lucide-vue-next';
import { t } from '@/i18n';
import { downloadCsv } from '@/utils/csv';
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

const columns = computed(() => [
  { key: 'created_at', label: t('common.date'), sortable: true },
  { key: 'order', label: t('paymentsPage.order') },
  { key: 'gateway', label: t('paymentsPage.gateway'), sortable: true },
  { key: 'amount', label: t('paymentsPage.amount'), align: 'right', sortable: true },
  { key: 'status', label: t('common.status'), sortable: true },
  { key: 'actions', label: '', align: 'right' }
]);

const { items, page, total, totalPages, loading, load } = usePaginated((params) => seller.paymentsManage(params));
const changePage = (n) => {
  page.value = n;
  load();
};

const exportCsv = () => {
  const rows = items.value.map((p) => ({
    date: (p.created_at || '').slice(0, 10),
    order: String(p.order).slice(0, 8),
    gateway: p.gateway,
    amount: p.amount,
    currency: p.currency,
    status: p.status,
    transaction_id: p.transaction_id || ''
  }));
  downloadCsv(`payments-${new Date().toISOString().slice(0, 10)}.csv`, rows);
};

const capture = async (p) => {
  acting.value = p.id;
  try {
    await seller.capturePayment(p.id);
    ui.success(t('paymentsPage.paymentCaptured'));
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
    <PageHeader :title="$t('paymentsPage.title')" :subtitle="$t('paymentsPage.subtitle')">
      <template #actions>
        <button class="btn btn-outline btn-sm" :disabled="!items.length" @click="exportCsv"><Download class="h-4 w-4" /> {{ $t('common.export') }}</button>
      </template>
    </PageHeader>

    <div v-if="gateways.length" class="mb-4 flex flex-wrap gap-2">
      <span v-for="g in gateways" :key="g.code" class="chip border-slate-200 bg-white text-ink"><CreditCard class="h-3.5 w-3.5 text-primary-600" /> {{ g.display_name || g.code }}</span>
    </div>

    <DataTable :columns="columns" :rows="items" :loading="loading" :empty-title="$t('paymentsPage.emptyTitle')" :empty-message="$t('paymentsPage.emptyMessage')">
      <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
      <template #cell-order="{ value }"><span class="font-mono text-xs">{{ String(value).slice(0, 8) }}</span></template>
      <template #cell-gateway="{ value }"><span class="capitalize">{{ value }}</span></template>
      <template #cell-amount="{ row }">{{ row.amount }} {{ row.currency }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <button v-if="tenant.canWrite && ['pending', 'authorized', 'requires_capture'].includes(row.status)" class="btn btn-ghost btn-sm text-emerald-600" :disabled="acting === row.id" @click="capture(row)">
          <CheckCheck class="h-4 w-4" /> {{ $t('paymentsPage.capture') }}
        </button>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6"><Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" /></div>
  </div>
</template>
