<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import VueApexCharts from 'vue3-apexcharts';
import {
  Store as StoreIcon,
  Package,
  Tags,
  Users,
  DollarSign,
  ShoppingBag,
  ExternalLink,
  LayoutGrid,
  Trophy,
  ArrowRight,
  RefreshCw,
  Crown,
  Coins
} from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useTenantStore } from '@/stores/tenant';
import { storefront } from '@/services/storefront';
import http from '@/services/http';

const router = useRouter();
const tenant = useTenantStore();

const loading = ref(true);
const stats = ref({ stores: 0, products: 0, categories: 0 });
const storeStats = ref([]);
const rollup = ref({ revenue: 0, orders: 0, pending: 0 });

const currency = computed(() => tenant.currency);

const kpis = computed(() => [
  { label: 'Total stores', value: stats.value.stores, icon: StoreIcon, tone: 'text-primary-600 bg-primary-50' },
  { label: 'Total products', value: stats.value.products, icon: Package, tone: 'text-sky-600 bg-sky-50' },
  { label: 'Categories', value: stats.value.categories, icon: Tags, tone: 'text-violet-600 bg-violet-50' },
  { label: 'My managed stores', value: tenant.stores.length, icon: Users, tone: 'text-emerald-600 bg-emerald-50' }
]);

const leaderboard = computed(() => [...storeStats.value].sort((a, b) => b.revenue - a.revenue).slice(0, 8));
const bestStore = computed(() => leaderboard.value[0] || null);
const avgPerStore = computed(() => {
  const n = tenant.stores.length || 1;
  return (Number(rollup.value.revenue) / n).toFixed(2);
});

const chartSeries = computed(() => [{ name: 'Revenue', data: leaderboard.value.map((s) => Number(s.revenue.toFixed(2))) }]);
const chartOptions = computed(() => ({
  chart: { type: 'bar', toolbar: { show: false } },
  plotOptions: { bar: { horizontal: true, borderRadius: 4, barHeight: '60%' } },
  colors: ['#F28B00'],
  dataLabels: { enabled: false },
  xaxis: { categories: leaderboard.value.map((s) => s.name), labels: { style: { colors: '#9a9a9a' } } },
  yaxis: { labels: { style: { colors: '#484848' } } },
  grid: { borderColor: '#f1f1f1' },
  tooltip: { y: { formatter: (v) => `${v} ${currency.value}` } }
}));

const load = async () => {
  loading.value = true;
  try {
    await tenant.ensureReady();
    const [st, pr, cat] = await Promise.all([
      storefront.stores({ page_size: 100 }),
      storefront.products({ page_size: 1 }),
      storefront.categories()
    ]);
    stats.value = {
      stores: st.$meta?.pagination?.count ?? (st.data?.results || st.data || []).length,
      products: pr.$meta?.pagination?.count ?? 0,
      categories: (cat.data || []).length
    };

    const results = await Promise.allSettled(
      tenant.stores.map((s) =>
        http
          .get('/analytics/dashboard/', { headers: { 'X-Store-Id': s.id } })
          .then((r) => ({ name: s.name, d: r.data }))
      )
    );
    let revenue = 0;
    let orders = 0;
    let pending = 0;
    const rows = [];
    results.forEach((r) => {
      if (r.status === 'fulfilled') {
        const o = r.value.d?.orders || {};
        const rev = Number(o.revenue || 0);
        revenue += rev;
        orders += Number(o.count || 0);
        pending += Number(o.pending || 0);
        rows.push({ name: r.value.name, revenue: rev, orders: Number(o.count || 0), pending: Number(o.pending || 0) });
      }
    });
    storeStats.value = rows;
    rollup.value = { revenue: revenue.toFixed(2), orders, pending };
  } finally {
    loading.value = false;
  }
};

const refreshing = ref(false);
const refresh = async () => {
  refreshing.value = true;
  try {
    await load();
  } finally {
    refreshing.value = false;
  }
};

onMounted(load);
</script>

<template>
  <div>
    <div v-if="loading" class="flex min-h-[50vh] items-center justify-center"><Spinner :size="30" label="Loading platform…" /></div>

    <template v-else>
      <PageHeader title="Platform overview" subtitle="Marketplace-wide performance across all stores.">
        <template #actions>
          <button class="btn btn-ghost btn-sm" :disabled="refreshing" @click="refresh"><RefreshCw class="h-4 w-4" :class="refreshing ? 'animate-spin' : ''" /> Refresh</button>
          <RouterLink :to="{ name: 'admin-platform' }" class="btn btn-outline btn-sm"><LayoutGrid class="h-4 w-4" /> All stores</RouterLink>
          <a href="/django-admin/" target="_blank" rel="noopener" class="btn btn-outline btn-sm"><ExternalLink class="h-4 w-4" /> Django admin</a>
        </template>
      </PageHeader>

      <!-- KPIs -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="k in kpis" :key="k.label" class="card p-5">
          <span class="grid h-10 w-10 place-items-center rounded-lg" :class="k.tone"><component :is="k.icon" class="h-5 w-5" /></span>
          <p class="mt-3 font-heading text-2xl font-bold">{{ k.value }}</p>
          <p class="text-sm text-muted">{{ k.label }}</p>
        </div>
      </div>

      <!-- Best store highlight -->
      <div v-if="bestStore && bestStore.revenue > 0" class="mt-6 flex items-center justify-between overflow-hidden rounded-xl bg-gradient-to-r from-ink to-primary-900 p-5 text-white">
        <div class="flex items-center gap-4">
          <span class="grid h-12 w-12 place-items-center rounded-xl bg-white/15"><Crown class="h-6 w-6 text-primary-400" /></span>
          <div>
            <p class="text-xs uppercase tracking-wide text-white/60">Top performing store</p>
            <p class="font-heading text-xl font-black">{{ bestStore.name }}</p>
          </div>
        </div>
        <div class="text-right">
          <p class="font-heading text-2xl font-black">{{ bestStore.revenue.toFixed(2) }} {{ currency }}</p>
          <p class="text-sm text-white/70">{{ bestStore.orders }} orders</p>
        </div>
      </div>

      <!-- Rollup -->
      <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-emerald-50 text-emerald-600"><DollarSign class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ rollup.revenue }} {{ currency }}</p><p class="text-sm text-muted">Total revenue</p></div>
        </div>
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-primary-50 text-primary-600"><Coins class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ avgPerStore }} {{ currency }}</p><p class="text-sm text-muted">Avg / store</p></div>
        </div>
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-sky-50 text-sky-600"><ShoppingBag class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ rollup.orders }}</p><p class="text-sm text-muted">Total orders</p></div>
        </div>
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-amber-50 text-amber-600"><ShoppingBag class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ rollup.pending }}</p><p class="text-sm text-muted">Orders pending</p></div>
        </div>
      </div>

      <!-- Leaderboard -->
      <div class="mt-8 grid gap-6 lg:grid-cols-2">
        <div class="card p-5">
          <h3 class="mb-4 flex items-center gap-2 font-heading font-semibold"><Trophy class="h-5 w-5 text-primary-600" /> Revenue by store</h3>
          <VueApexCharts v-if="leaderboard.some((s) => s.revenue > 0)" type="bar" height="320" :options="chartOptions" :series="chartSeries" />
          <EmptyState v-else title="No revenue yet" message="Store revenue will rank here once orders are confirmed." />
        </div>
        <div class="card p-5">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="font-heading font-semibold">Store leaderboard</h3>
            <RouterLink :to="{ name: 'admin-platform' }" class="text-sm font-medium text-primary-600 hover:underline">Manage <ArrowRight class="inline h-3.5 w-3.5" /></RouterLink>
          </div>
          <ul v-if="leaderboard.length" class="space-y-3">
            <li v-for="(s, i) in leaderboard" :key="s.name" class="flex items-center gap-3">
              <span class="grid h-7 w-7 shrink-0 place-items-center rounded-md text-xs font-bold" :class="i === 0 ? 'bg-primary-600 text-white' : 'bg-slate-100 text-slate-500'">{{ i + 1 }}</span>
              <span class="flex-1 truncate text-sm font-medium">{{ s.name }}</span>
              <span class="text-xs text-slate-400">{{ s.orders }} orders</span>
              <span class="text-sm font-semibold">{{ s.revenue.toFixed(2) }} {{ currency }}</span>
            </li>
          </ul>
          <EmptyState v-else title="No stores" message="No manageable stores yet." />
        </div>
      </div>
    </template>
  </div>
</template>
