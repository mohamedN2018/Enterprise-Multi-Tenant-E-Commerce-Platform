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
import { t } from '@/i18n';
import { useTheme } from '@/theme';

const router = useRouter();
const tenant = useTenantStore();
const { theme } = useTheme();
const axisColor = computed(() => (theme.value === 'dark' ? '#94a3b8' : '#9a9a9a'));
const gridColor = computed(() => (theme.value === 'dark' ? '#334155' : '#f1f1f1'));

const loading = ref(true);
const stats = ref({ stores: 0, products: 0, categories: 0 });
const storeStats = ref([]);
const rollup = ref({ revenue: 0, orders: 0, pending: 0 });

const currency = computed(() => tenant.currency);

const kpis = computed(() => [
  { label: t('dash.totalStores'), value: stats.value.stores, icon: StoreIcon, tone: 'text-primary-600 bg-primary-50' },
  { label: t('dash.totalProducts'), value: stats.value.products, icon: Package, tone: 'text-sky-600 bg-sky-50' },
  { label: t('dash.categories'), value: stats.value.categories, icon: Tags, tone: 'text-violet-600 bg-violet-50' },
  { label: t('dash.myManagedStores'), value: tenant.stores.length, icon: Users, tone: 'text-emerald-600 bg-emerald-50' }
]);

const leaderboard = computed(() => [...storeStats.value].sort((a, b) => b.revenue - a.revenue).slice(0, 8));
const bestStore = computed(() => leaderboard.value[0] || null);
const avgPerStore = computed(() => {
  const n = tenant.stores.length || 1;
  return (Number(rollup.value.revenue) / n).toFixed(2);
});

const chartSeries = computed(() => [{ name: t('dash.revenue'), data: leaderboard.value.map((s) => Number(s.revenue.toFixed(2))) }]);
const chartOptions = computed(() => ({
  chart: { type: 'bar', toolbar: { show: false } },
  plotOptions: { bar: { horizontal: true, borderRadius: 4, barHeight: '60%' } },
  colors: ['#F28B00'],
  dataLabels: { enabled: false },
  xaxis: { categories: leaderboard.value.map((s) => s.name), labels: { style: { colors: axisColor.value } } },
  yaxis: { labels: { style: { colors: axisColor.value } } },
  grid: { borderColor: gridColor.value },
  tooltip: { theme: theme.value, y: { formatter: (v) => `${v} ${currency.value}` } }
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
    <div v-if="loading" class="flex min-h-[50vh] items-center justify-center"><Spinner :size="30" :label="$t('dash.loadingPlatform')" /></div>

    <template v-else>
      <PageHeader :title="$t('dash.platformOverview')" :subtitle="$t('dash.platformSubtitle')">
        <template #actions>
          <button class="btn btn-ghost btn-sm" :disabled="refreshing" @click="refresh"><RefreshCw class="h-4 w-4" :class="refreshing ? 'animate-spin' : ''" /> {{ $t('dash.refresh') }}</button>
          <RouterLink :to="{ name: 'admin-platform' }" class="btn btn-outline btn-sm"><LayoutGrid class="h-4 w-4" /> {{ $t('dash.allStores') }}</RouterLink>
          <a href="/django-admin/" target="_blank" rel="noopener" class="btn btn-outline btn-sm"><ExternalLink class="h-4 w-4" /> {{ $t('dash.djangoAdmin') }}</a>
        </template>
      </PageHeader>

      <!-- KPIs -->
      <div class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
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
            <p class="text-xs uppercase tracking-wide text-white/60">{{ $t('dash.topStore') }}</p>
            <p class="font-heading text-xl font-black">{{ bestStore.name }}</p>
          </div>
        </div>
        <div class="text-end">
          <p class="font-heading text-2xl font-black">{{ bestStore.revenue.toFixed(2) }} {{ currency }}</p>
          <p class="text-sm text-white/70">{{ bestStore.orders }} {{ $t('dash.ordersLabel') }}</p>
        </div>
      </div>

      <!-- Rollup -->
      <div class="mt-6 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-emerald-50 text-emerald-600"><DollarSign class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ rollup.revenue }} {{ currency }}</p><p class="text-sm text-muted">{{ $t('dash.totalRevenue') }}</p></div>
        </div>
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-primary-50 text-primary-600"><Coins class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ avgPerStore }} {{ currency }}</p><p class="text-sm text-muted">{{ $t('dash.avgPerStore') }}</p></div>
        </div>
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-sky-50 text-sky-600"><ShoppingBag class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ rollup.orders }}</p><p class="text-sm text-muted">{{ $t('dash.totalOrders') }}</p></div>
        </div>
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-amber-50 text-amber-600"><ShoppingBag class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ rollup.pending }}</p><p class="text-sm text-muted">{{ $t('dash.ordersPending') }}</p></div>
        </div>
      </div>

      <!-- Leaderboard -->
      <div class="mt-8 grid gap-6 lg:grid-cols-2">
        <div class="card p-5">
          <h3 class="mb-4 flex items-center gap-2 font-heading font-semibold"><Trophy class="h-5 w-5 text-primary-600" /> {{ $t('dash.revenueByStore') }}</h3>
          <VueApexCharts v-if="leaderboard.some((s) => s.revenue > 0)" type="bar" height="320" :options="chartOptions" :series="chartSeries" />
          <EmptyState v-else :title="$t('dash.noRevenue')" :message="$t('dash.noRevenueMsg')" />
        </div>
        <div class="card p-5">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="font-heading font-semibold">{{ $t('dash.storeLeaderboard') }}</h3>
            <RouterLink :to="{ name: 'admin-platform' }" class="text-sm font-medium text-primary-600 hover:underline">{{ $t('dash.manage') }} <ArrowRight class="inline h-3.5 w-3.5 rtl:rotate-180" /></RouterLink>
          </div>
          <ul v-if="leaderboard.length" class="space-y-3">
            <li v-for="(s, i) in leaderboard" :key="s.name" class="flex items-center gap-3">
              <span class="grid h-7 w-7 shrink-0 place-items-center rounded-md text-xs font-bold" :class="i === 0 ? 'bg-primary-600 text-white' : 'bg-slate-100 text-slate-500'">{{ i + 1 }}</span>
              <span class="flex-1 truncate text-sm font-medium">{{ s.name }}</span>
              <span class="text-xs text-slate-400">{{ s.orders }} {{ $t('dash.ordersLabel') }}</span>
              <span class="text-sm font-semibold">{{ s.revenue.toFixed(2) }} {{ currency }}</span>
            </li>
          </ul>
          <EmptyState v-else :title="$t('dash.noStoresManage')" :message="$t('dash.noStoresManageMsg')" />
        </div>
      </div>
    </template>
  </div>
</template>
