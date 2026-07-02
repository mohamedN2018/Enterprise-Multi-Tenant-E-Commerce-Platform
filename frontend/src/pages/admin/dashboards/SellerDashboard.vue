<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import VueApexCharts from 'vue3-apexcharts';
import {
  DollarSign,
  ShoppingBag,
  TrendingUp,
  Users,
  Package,
  AlertTriangle,
  Star,
  Wallet,
  Plus,
  BadgePercent,
  ExternalLink,
  UsersRound,
  Clock,
  MessageSquare,
  ArrowRight
} from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';

const router = useRouter();
const tenant = useTenantStore();
const ui = useUiStore();

const loading = ref(true);
const dash = ref(null);

const currency = computed(() => dash.value?.payout_currency || tenant.currency);

const kpis = computed(() => {
  if (!dash.value) return [];
  const d = dash.value;
  return [
    { label: 'Revenue', value: `${d.orders.revenue} ${currency.value}`, icon: DollarSign, tone: 'text-emerald-600 bg-emerald-50' },
    { label: 'Orders', value: d.orders.count, sub: `${d.orders.pending} pending`, icon: ShoppingBag, tone: 'text-sky-600 bg-sky-50' },
    { label: 'Avg. order value', value: `${d.orders.aov} ${currency.value}`, icon: TrendingUp, tone: 'text-primary-600 bg-primary-50' },
    { label: 'Customers', value: d.customers, icon: Users, tone: 'text-violet-600 bg-violet-50' },
    { label: 'Products', value: d.catalog.products, sub: `${d.catalog.published} published`, icon: Package, tone: 'text-indigo-600 bg-indigo-50' },
    { label: 'Low stock', value: d.catalog.low_stock, icon: AlertTriangle, tone: 'text-amber-600 bg-amber-50' },
    { label: 'Avg. rating', value: (d.reviews.average || 0).toFixed(1), sub: `${d.reviews.pending} to moderate`, icon: Star, tone: 'text-amber-600 bg-amber-50' },
    { label: 'Payout balance', value: `${d.payout_balance} ${currency.value}`, icon: Wallet, tone: 'text-emerald-600 bg-emerald-50' }
  ];
});

const attention = computed(() => {
  if (!dash.value) return [];
  const d = dash.value;
  return [
    { label: 'Orders pending', value: d.orders.pending, icon: Clock, tone: 'bg-amber-50 text-amber-700', to: { name: 'admin-orders' } },
    { label: 'Low-stock items', value: d.catalog.low_stock, icon: AlertTriangle, tone: 'bg-secondary-50 text-secondary-700', to: { name: 'admin-inventory' } },
    { label: 'Reviews to moderate', value: d.reviews.pending, icon: MessageSquare, tone: 'bg-sky-50 text-sky-700', to: { name: 'admin-reviews' } }
  ];
});

const quickActions = computed(() => {
  const acts = [];
  if (tenant.canWrite) {
    acts.push({ label: 'Add product', icon: Plus, to: { name: 'admin-products' } });
    acts.push({ label: 'New coupon', icon: BadgePercent, to: { name: 'admin-promotions' } });
  }
  if (tenant.canManageMembers) acts.push({ label: 'Invite team', icon: UsersRound, to: { name: 'admin-team' } });
  acts.push({ label: 'View storefront', icon: ExternalLink, to: { name: 'home' } });
  return acts;
});

const revenueSeries = computed(() => [{ name: 'Revenue', data: (dash.value?.revenue_series || []).map((r) => Number(r.revenue)) }]);
const revenueOptions = computed(() => ({
  chart: { type: 'area', toolbar: { show: false } },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
  colors: ['#F28B00'],
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.35, opacityTo: 0.05 } },
  xaxis: { categories: (dash.value?.revenue_series || []).map((r) => r.date.slice(5)), labels: { style: { colors: '#9a9a9a' } }, axisBorder: { show: false }, axisTicks: { show: false } },
  yaxis: { labels: { style: { colors: '#9a9a9a' } } },
  grid: { borderColor: '#f1f1f1' },
  tooltip: { y: { formatter: (v) => `${v} ${currency.value}` } }
}));

const statusSeries = computed(() => {
  const o = dash.value?.orders;
  return o ? [o.confirmed, o.pending, o.cancelled] : [];
});
const statusOptions = {
  chart: { type: 'donut' },
  labels: ['Confirmed', 'Pending', 'Cancelled'],
  colors: ['#10b981', '#F28B00', '#F92400'],
  legend: { position: 'bottom' },
  dataLabels: { enabled: false },
  stroke: { width: 0 }
};

onMounted(async () => {
  try {
    await tenant.ensureReady();
    const res = await seller.dashboard();
    dash.value = res.data;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <div v-if="loading" class="flex min-h-[50vh] items-center justify-center"><Spinner :size="30" label="Loading dashboard…" /></div>

    <template v-else>
      <PageHeader title="Dashboard" :subtitle="tenant.active?.name">
        <template #actions>
          <span class="chip border-0 bg-primary-100 text-primary-700">{{ tenant.roleLabel }}</span>
        </template>
      </PageHeader>

      <!-- Quick actions -->
      <div class="mb-6 flex flex-wrap gap-3">
        <RouterLink v-for="a in quickActions" :key="a.label" :to="a.to" class="btn btn-outline btn-sm">
          <component :is="a.icon" class="h-4 w-4" /> {{ a.label }}
        </RouterLink>
      </div>

      <!-- Needs attention -->
      <div class="mb-6 grid gap-4 sm:grid-cols-3">
        <RouterLink v-for="a in attention" :key="a.label" :to="a.to" class="card flex items-center justify-between p-5 transition hover:shadow-pop">
          <div class="flex items-center gap-3">
            <span class="grid h-11 w-11 place-items-center rounded-lg" :class="a.tone"><component :is="a.icon" class="h-5 w-5" /></span>
            <div>
              <p class="font-heading text-2xl font-bold">{{ a.value }}</p>
              <p class="text-sm text-muted">{{ a.label }}</p>
            </div>
          </div>
          <ArrowRight class="h-5 w-5 text-slate-300" />
        </RouterLink>
      </div>

      <!-- KPIs -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="k in kpis" :key="k.label" class="card p-5">
          <span class="grid h-10 w-10 place-items-center rounded-lg" :class="k.tone"><component :is="k.icon" class="h-5 w-5" /></span>
          <p class="mt-3 font-heading text-2xl font-bold">{{ k.value }}</p>
          <p class="text-sm text-muted">{{ k.label }}</p>
          <p v-if="k.sub" class="mt-0.5 text-xs text-slate-400">{{ k.sub }}</p>
        </div>
      </div>

      <!-- Charts -->
      <div class="mt-6 grid gap-6 lg:grid-cols-3">
        <div class="card p-5 lg:col-span-2">
          <h3 class="mb-4 font-heading font-semibold">Revenue · last 14 days</h3>
          <VueApexCharts type="area" height="280" :options="revenueOptions" :series="revenueSeries" />
        </div>
        <div class="card p-5">
          <h3 class="mb-4 font-heading font-semibold">Orders by status</h3>
          <VueApexCharts v-if="statusSeries.some((n) => n > 0)" type="donut" height="280" :options="statusOptions" :series="statusSeries" />
          <EmptyState v-else title="No orders yet" message="Order breakdown will appear here." />
        </div>
      </div>

      <!-- Recent + Top -->
      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <div class="card p-5">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="font-heading font-semibold">Recent orders</h3>
            <RouterLink :to="{ name: 'admin-orders' }" class="text-sm font-medium text-primary-600 hover:underline">View all</RouterLink>
          </div>
          <ul v-if="dash?.recent_orders?.length" class="divide-y divide-slate-100">
            <li v-for="o in dash.recent_orders" :key="o.number" class="flex items-center justify-between py-3">
              <div>
                <p class="text-sm font-medium">#{{ o.number }}</p>
                <p class="text-xs text-slate-400">{{ (o.created_at || '').slice(0, 10) }}</p>
              </div>
              <div class="flex items-center gap-3">
                <StatusBadge :status="o.status" />
                <span class="text-sm font-semibold">{{ o.total }} {{ o.currency }}</span>
              </div>
            </li>
          </ul>
          <EmptyState v-else title="No orders yet" message="New orders will show up here." />
        </div>

        <div class="card p-5">
          <h3 class="mb-4 font-heading font-semibold">Top products</h3>
          <ul v-if="dash?.top_products?.length" class="space-y-3">
            <li v-for="(t, i) in dash.top_products" :key="t.name" class="flex items-center gap-3">
              <span class="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-slate-100 text-xs font-bold text-slate-500">{{ i + 1 }}</span>
              <span class="flex-1 truncate text-sm font-medium">{{ t.name }}</span>
              <span class="text-xs text-slate-400">{{ t.units }} sold</span>
              <span class="text-sm font-semibold">{{ t.revenue }} {{ currency }}</span>
            </li>
          </ul>
          <EmptyState v-else title="No sales yet" message="Your best sellers will appear here." />
        </div>
      </div>
    </template>
  </div>
</template>
