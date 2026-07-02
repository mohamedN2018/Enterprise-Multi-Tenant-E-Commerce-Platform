<script setup>
import { ref, computed, onMounted } from 'vue';
import {
  DollarSign,
  ShoppingBag,
  TrendingUp,
  Users,
  Package,
  AlertTriangle,
  Star,
  Wallet,
  Store as StoreIcon,
  Plus
} from 'lucide-vue-next';
import VueApexCharts from 'vue3-apexcharts';
import PageHeader from '@/components/ui/PageHeader.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Spinner from '@/components/ui/Spinner.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';

const tenant = useTenantStore();
const ui = useUiStore();

const loading = ref(true);
const dash = ref(null);

const showCreate = ref(false);
const creating = ref(false);
const form = ref({ name: '', currency: 'USD', country: '', description: '' });

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

const revenueSeries = computed(() => [
  { name: 'Revenue', data: (dash.value?.revenue_series || []).map((r) => Number(r.revenue)) }
]);
const revenueOptions = computed(() => ({
  chart: { type: 'area', toolbar: { show: false }, sparkline: { enabled: false } },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
  colors: ['#4f46e5'],
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.35, opacityTo: 0.05 } },
  xaxis: {
    categories: (dash.value?.revenue_series || []).map((r) => r.date.slice(5)),
    labels: { style: { colors: '#94a3b8' } },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: { labels: { style: { colors: '#94a3b8' } } },
  grid: { borderColor: '#f1f5f9' },
  tooltip: { y: { formatter: (v) => `${v} ${currency.value}` } }
}));

const statusSeries = computed(() => {
  const o = dash.value?.orders;
  return o ? [o.confirmed, o.pending, o.cancelled] : [];
});
const statusOptions = {
  chart: { type: 'donut' },
  labels: ['Confirmed', 'Pending', 'Cancelled'],
  colors: ['#10b981', '#f59e0b', '#ef4444'],
  legend: { position: 'bottom' },
  dataLabels: { enabled: false },
  stroke: { width: 0 }
};

const load = async () => {
  loading.value = true;
  try {
    const id = await tenant.ensureReady();
    if (!id) {
      loading.value = false;
      return;
    }
    const res = await seller.dashboard();
    dash.value = res.data;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

const createStore = async () => {
  creating.value = true;
  try {
    const res = await seller.createStore(form.value);
    ui.success('Store created!');
    showCreate.value = false;
    await tenant.refresh();
    tenant.select(res.data.id);
    await load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    creating.value = false;
  }
};

onMounted(load);
</script>

<template>
  <div>
    <div v-if="loading" class="flex min-h-[50vh] items-center justify-center">
      <Spinner :size="30" label="Loading dashboard…" />
    </div>

    <!-- No store yet -->
    <div v-else-if="!tenant.hasStores">
      <PageHeader title="Welcome to your Seller Center" subtitle="Create your first store to start selling." />
      <EmptyState :icon="StoreIcon" title="You don't have a store yet" message="Open a store to add products, manage orders and grow your business.">
        <button class="btn btn-primary" @click="showCreate = true"><Plus class="h-4 w-4" /> Create store</button>
      </EmptyState>
    </div>

    <template v-else>
      <PageHeader title="Dashboard" :subtitle="tenant.active?.name">
        <template #actions>
          <button class="btn btn-outline btn-sm" @click="showCreate = true"><Plus class="h-4 w-4" /> New store</button>
        </template>
      </PageHeader>

      <!-- KPIs -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="k in kpis" :key="k.label" class="card p-5">
          <div class="flex items-center justify-between">
            <span class="grid h-10 w-10 place-items-center rounded-lg" :class="k.tone">
              <component :is="k.icon" class="h-5 w-5" />
            </span>
          </div>
          <p class="mt-3 text-2xl font-bold">{{ k.value }}</p>
          <p class="text-sm text-slate-500">{{ k.label }}</p>
          <p v-if="k.sub" class="mt-0.5 text-xs text-slate-400">{{ k.sub }}</p>
        </div>
      </div>

      <!-- Charts -->
      <div class="mt-6 grid gap-6 lg:grid-cols-3">
        <div class="card p-5 lg:col-span-2">
          <h3 class="mb-4 font-semibold">Revenue · last 14 days</h3>
          <VueApexCharts type="area" height="280" :options="revenueOptions" :series="revenueSeries" />
        </div>
        <div class="card p-5">
          <h3 class="mb-4 font-semibold">Orders by status</h3>
          <VueApexCharts v-if="statusSeries.some((n) => n > 0)" type="donut" height="280" :options="statusOptions" :series="statusSeries" />
          <EmptyState v-else title="No orders yet" message="Order breakdown will appear here." />
        </div>
      </div>

      <!-- Recent + Top -->
      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <div class="card p-5">
          <h3 class="mb-4 font-semibold">Recent orders</h3>
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
          <h3 class="mb-4 font-semibold">Top products</h3>
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

    <!-- Create store modal -->
    <Modal v-model="showCreate" title="Create a new store">
      <form id="create-store" class="grid gap-4" @submit.prevent="createStore">
        <FormField v-model="form.name" label="Store name" placeholder="Acme Supplies" required />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="form.currency" label="Currency" placeholder="USD" maxlength="3" />
          <FormField v-model="form.country" label="Country (ISO-2)" placeholder="US" maxlength="2" />
        </div>
        <FormField v-model="form.description" label="Description" placeholder="What do you sell?" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showCreate = false">Cancel</button>
          <button form="create-store" type="submit" class="btn btn-primary" :disabled="creating">
            <Spinner v-if="creating" :size="18" /><span v-else>Create store</span>
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
