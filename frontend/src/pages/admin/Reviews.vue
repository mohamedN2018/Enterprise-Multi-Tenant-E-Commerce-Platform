<script setup>
import { ref, onMounted } from 'vue';
import { Check, X, Star, Download } from 'lucide-vue-next';
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

const statusFilter = ref('pending');
const productMap = ref({});
const acting = ref(null);

const tabs = [
  { key: 'pending', label: 'Pending' },
  { key: 'approved', label: 'Approved' },
  { key: 'rejected', label: 'Rejected' },
  { key: '', label: 'All' }
];

const columns = [
  { key: 'product', label: 'Product' },
  { key: 'rating', label: 'Rating' },
  { key: 'body', label: 'Review' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '', align: 'right' }
];

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  seller.reviewsModeration(params)
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

const moderate = async (review, approve) => {
  acting.value = review.id;
  try {
    if (approve) await seller.approveReview(review.id);
    else await seller.rejectReview(review.id);
    ui.success(approve ? 'Review approved.' : 'Review rejected.');
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    acting.value = null;
  }
};

const exportCsv = () => {
  const rows = items.value.map((r) => ({
    product: productMap.value[r.product] || 'Product',
    rating: r.rating,
    title: r.title || '',
    status: r.status,
    date: (r.created_at || '').slice(0, 10)
  }));
  downloadCsv(`reviews-${new Date().toISOString().slice(0, 10)}.csv`, rows);
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (!id) return;
  try {
    const prod = await seller.products({ page_size: 100 });
    const list = prod.data?.results || prod.data || [];
    productMap.value = Object.fromEntries(list.map((p) => [p.id, p.name]));
  } catch {
    productMap.value = {};
  }
  fetch();
});
</script>

<template>
  <div>
    <PageHeader title="Reviews" subtitle="Moderate customer reviews for your store.">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">Read-only</span>
        <button class="btn btn-outline btn-sm" :disabled="!items.length" @click="exportCsv"><Download class="h-4 w-4" /> Export</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex flex-wrap gap-2">
      <button
        v-for="t in tabs"
        :key="t.label"
        class="rounded-full px-4 py-1.5 text-sm font-medium transition"
        :class="statusFilter === t.key ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'"
        @click="selectTab(t.key)"
      >
        {{ t.label }}
      </button>
    </div>

    <DataTable :columns="columns" :rows="items" :loading="loading" empty-title="No reviews" empty-message="Reviews awaiting moderation will appear here.">
      <template #cell-product="{ value }">
        <span class="font-medium text-ink">{{ productMap[value] || 'Product' }}</span>
      </template>
      <template #cell-rating="{ row }">
        <div class="flex">
          <Star v-for="n in 5" :key="n" class="h-4 w-4" :class="n <= row.rating ? 'fill-primary-600 text-primary-600' : 'text-slate-300'" />
        </div>
      </template>
      <template #cell-body="{ row }">
        <div class="max-w-md">
          <p v-if="row.title" class="font-medium text-ink">{{ row.title }}</p>
          <p class="clamp-2 text-sm text-muted">{{ row.body || '—' }}</p>
        </div>
      </template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <div v-if="tenant.canWrite && row.status === 'pending'" class="flex justify-end gap-1">
          <button class="btn btn-ghost btn-sm text-emerald-600" :disabled="acting === row.id" @click="moderate(row, true)"><Check class="h-4 w-4" /> Approve</button>
          <button class="btn btn-ghost btn-sm text-secondary-500" :disabled="acting === row.id" @click="moderate(row, false)"><X class="h-4 w-4" /> Reject</button>
        </div>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6">
      <Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" />
    </div>
  </div>
</template>
