<script setup>
import { ref, computed, onMounted } from 'vue';
import { Check, X, Banknote, Download } from 'lucide-vue-next';
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
import { t } from '@/i18n';

const tenant = useTenantStore();
const ui = useUiStore();

const statusFilter = ref('');
const acting = ref(null);

const tabs = computed(() => [
  { key: '', label: t('common.all') },
  { key: 'requested', label: t('status.requested') },
  { key: 'approved', label: t('status.approved') },
  { key: 'rejected', label: t('status.rejected') },
  { key: 'refunded', label: t('status.refunded') }
]);

const columns = computed(() => [
  { key: 'created_at', label: t('common.date'), sortable: true },
  { key: 'order', label: t('returnsPage.order') },
  { key: 'resolution', label: t('returnsPage.resolution'), sortable: true },
  { key: 'reason', label: t('returnsPage.reason') },
  { key: 'refund_amount', label: t('returnsPage.refund'), align: 'right', sortable: true },
  { key: 'status', label: t('common.status'), sortable: true },
  { key: 'actions', label: '', align: 'right' }
]);

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  seller.returnsManage(params)
);
const fetch = () => load(statusFilter.value ? { status: statusFilter.value } : {});
const changePage = (n) => {
  page.value = n;
  fetch();
};
const selectTab = (key) => {
  statusFilter.value = key;
  page.value = 1;
  fetch();
};

const run = async (r, fn, label) => {
  acting.value = r.id;
  try {
    await fn();
    ui.success(label);
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    acting.value = null;
  }
};
const approve = (r) => run(r, () => seller.approveReturn(r.id), t('returnsPage.approvedToast'));
const reject = (r) => run(r, () => seller.rejectReturn(r.id, { reason: '' }), t('returnsPage.rejectedToast'));
const refund = (r) => run(r, () => seller.refundReturn(r.id), t('returnsPage.refundIssued'));

const exportCsv = () => {
  const rows = items.value.map((r) => ({
    date: (r.created_at || '').slice(0, 10),
    order: String(r.order).slice(0, 8),
    resolution: r.resolution,
    reason: r.reason || '',
    refund_amount: r.refund_amount,
    status: r.status
  }));
  downloadCsv(`returns-${new Date().toISOString().slice(0, 10)}.csv`, rows);
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) fetch();
});
</script>

<template>
  <div>
    <PageHeader :title="$t('returnsPage.title')" :subtitle="$t('returnsPage.subtitle')">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('common.readOnly') }}</span>
        <button class="btn btn-outline btn-sm" :disabled="!items.length" @click="exportCsv"><Download class="h-4 w-4" /> {{ $t('common.export') }}</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex flex-wrap gap-2">
      <button v-for="t in tabs" :key="t.key" class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="statusFilter === t.key ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="selectTab(t.key)">{{ t.label }}</button>
    </div>

    <DataTable :columns="columns" :rows="items" :loading="loading" :empty-title="$t('returnsPage.emptyTitle')" :empty-message="$t('returnsPage.emptyMsg')">
      <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
      <template #cell-order="{ value }"><span class="font-mono text-xs">{{ String(value).slice(0, 8) }}</span></template>
      <template #cell-resolution="{ value }"><span class="capitalize">{{ String(value).replace(/_/g, ' ') }}</span></template>
      <template #cell-reason="{ value }"><span class="clamp-1 block max-w-xs text-sm text-muted">{{ value || '—' }}</span></template>
      <template #cell-refund_amount="{ value }">{{ Number(value) > 0 ? `${value} ${tenant.currency}` : '—' }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <div v-if="tenant.canWrite" class="flex justify-end gap-1">
          <template v-if="row.status === 'requested'">
            <button class="btn btn-ghost btn-sm text-emerald-600" :disabled="acting === row.id" @click="approve(row)"><Check class="h-4 w-4" /> {{ $t('returnsPage.approve') }}</button>
            <button class="btn btn-ghost btn-sm text-secondary-500" :disabled="acting === row.id" @click="reject(row)"><X class="h-4 w-4" /> {{ $t('returnsPage.reject') }}</button>
          </template>
          <button v-else-if="row.status === 'approved'" class="btn btn-ghost btn-sm text-primary-600" :disabled="acting === row.id" @click="refund(row)"><Banknote class="h-4 w-4" /> {{ $t('returnsPage.refundAction') }}</button>
          <span v-else class="text-xs text-muted">—</span>
        </div>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6"><Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" /></div>
  </div>
</template>
