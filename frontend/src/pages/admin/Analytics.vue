<script setup>
import { ref, computed, onMounted } from 'vue';
import { Activity, ShoppingBag, DollarSign, BarChart3 } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import DataTable from '@/components/ui/DataTable.vue';
import Pagination from '@/components/ui/Pagination.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useTenantStore } from '@/stores/tenant';
import { usePaginated } from '@/composables/usePaginated';
import { seller } from '@/services/seller';

const tenant = useTenantStore();

const loading = ref(true);
const summary = ref(null);

const kpis = computed(() => {
  const s = summary.value;
  if (!s) return [];
  return [
    { label: 'Total events', value: s.total_events ?? 0, icon: Activity, tone: 'text-primary-600 bg-primary-50' },
    { label: 'Orders', value: s.orders?.count ?? 0, icon: ShoppingBag, tone: 'text-sky-600 bg-sky-50' },
    { label: 'Confirmed', value: s.orders?.confirmed ?? 0, icon: ShoppingBag, tone: 'text-emerald-600 bg-emerald-50' },
    { label: 'Revenue', value: `${s.orders?.revenue ?? '0.00'} ${tenant.currency}`, icon: DollarSign, tone: 'text-emerald-600 bg-emerald-50' }
  ];
});

const eventTypes = computed(() => {
  const ev = summary.value?.events || {};
  const entries = Object.entries(ev);
  const max = Math.max(1, ...entries.map(([, v]) => Number(v)));
  return entries.sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ type: k, count: v, pct: (Number(v) / max) * 100 }));
});

const columns = [
  { key: 'occurred_at', label: 'When', sortable: true },
  { key: 'event_type', label: 'Event', sortable: true },
  { key: 'user', label: 'User' }
];

const { items, page, total, totalPages, loading: eventsLoading, load } = usePaginated((params) => seller.analyticsEvents(params));
const changePage = (n) => {
  page.value = n;
  load();
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (!id) {
    loading.value = false;
    return;
  }
  try {
    const s = await seller.analyticsSummary();
    summary.value = s.data;
  } catch {
    summary.value = null;
  } finally {
    loading.value = false;
  }
  load();
});
</script>

<template>
  <div>
    <PageHeader title="Analytics" subtitle="Store activity and event insights." />

    <div v-if="loading" class="flex min-h-[30vh] items-center justify-center"><Spinner :size="28" label="Loading…" /></div>

    <template v-else>
      <!-- KPIs -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="k in kpis" :key="k.label" class="card p-5">
          <span class="grid h-10 w-10 place-items-center rounded-lg" :class="k.tone"><component :is="k.icon" class="h-5 w-5" /></span>
          <p class="mt-3 font-heading text-2xl font-bold">{{ k.value }}</p>
          <p class="text-sm text-muted">{{ k.label }}</p>
        </div>
      </div>

      <!-- Events by type -->
      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <div class="card p-5">
          <h3 class="mb-4 flex items-center gap-2 font-heading font-semibold"><BarChart3 class="h-5 w-5 text-primary-600" /> Events by type</h3>
          <ul v-if="eventTypes.length" class="space-y-3">
            <li v-for="e in eventTypes" :key="e.type">
              <div class="mb-1 flex items-center justify-between text-sm">
                <span class="capitalize text-ink">{{ String(e.type).replace(/_/g, ' ') }}</span>
                <span class="font-medium text-muted">{{ e.count }}</span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-slate-100"><div class="h-full rounded-full bg-primary-600" :style="{ width: `${e.pct}%` }"></div></div>
            </li>
          </ul>
          <p v-else class="text-sm text-muted">No events recorded yet.</p>
        </div>

        <!-- Event feed -->
        <div class="card p-0">
          <h3 class="flex items-center gap-2 border-b border-slate-100 p-5 font-heading font-semibold"><Activity class="h-5 w-5 text-primary-600" /> Recent events</h3>
          <DataTable :columns="columns" :rows="items" :loading="eventsLoading" empty-title="No events" empty-message="Activity will be logged here.">
            <template #cell-occurred_at="{ row }">{{ (row.occurred_at || row.created_at || '').replace('T', ' ').slice(0, 16) }}</template>
            <template #cell-event_type="{ value }"><span class="capitalize">{{ String(value).replace(/_/g, ' ') }}</span></template>
            <template #cell-user="{ value }"><span class="font-mono text-xs">{{ value ? String(value).slice(0, 8) : 'guest' }}</span></template>
          </DataTable>
        </div>
      </div>

      <div v-if="totalPages > 1" class="mt-6"><Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" /></div>
    </template>
  </div>
</template>
