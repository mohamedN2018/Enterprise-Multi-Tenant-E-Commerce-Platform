<script setup>
import { ref, computed, onMounted } from 'vue';
import {
  Clock,
  AlertTriangle,
  Package,
  Star,
  ShoppingBag,
  Boxes,
  Tags,
  ArrowRight,
  Eye
} from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useAuthStore } from '@/stores/auth';
import { useTenantStore } from '@/stores/tenant';
import { seller } from '@/services/seller';
import { t } from '@/i18n';

const auth = useAuthStore();
const tenant = useTenantStore();

const loading = ref(true);
const dash = ref(null);
const lowStock = ref([]);

const metrics = computed(() => {
  if (!dash.value) return [];
  const d = dash.value;
  return [
    { label: t('dash.ordersToProcess'), value: d.orders.pending, icon: Clock, tone: 'bg-amber-50 text-amber-700' },
    { label: t('dash.lowStockItems'), value: d.catalog.low_stock, icon: AlertTriangle, tone: 'bg-secondary-50 text-secondary-700' },
    { label: t('dash.publishedProducts'), value: d.catalog.published, icon: Package, tone: 'bg-primary-50 text-primary-700' },
    { label: t('dash.storeRating'), value: (d.reviews.average || 0).toFixed(1), icon: Star, tone: 'bg-sky-50 text-sky-700' }
  ];
});

const shortcuts = computed(() => [
  { label: t('dash.orders'), desc: t('dash.reviewIncoming'), icon: ShoppingBag, to: { name: 'admin-orders' } },
  { label: t('dash.products'), desc: t('dash.browseCatalog'), icon: Package, to: { name: 'admin-products' } },
  { label: t('dash.inventory'), desc: t('dash.checkStock'), icon: Boxes, to: { name: 'admin-inventory' } },
  { label: t('dash.categories'), desc: t('dash.viewCategories'), icon: Tags, to: { name: 'admin-categories' } }
]);

onMounted(async () => {
  try {
    await tenant.ensureReady();
    const res = await seller.dashboard();
    dash.value = res.data;
    seller.lowStock().then((r) => (lowStock.value = (r.data?.results || r.data || []).slice(0, 8))).catch(() => (lowStock.value = []));
  } catch {
    dash.value = null;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <div v-if="loading" class="flex min-h-[50vh] items-center justify-center"><Spinner :size="30" :label="$t('admin.loading')" /></div>

    <template v-else>
      <PageHeader :title="$t('dash.hi', { name: auth.displayName })" :subtitle="`${tenant.active?.name} · ${$t('dash.staffView')}`">
        <template #actions>
          <span class="chip border-0 bg-slate-100 text-slate-600">{{ $t('dash.employeeReadonly') }}</span>
        </template>
      </PageHeader>

      <!-- Operational snapshot -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="m in metrics" :key="m.label" class="card p-5">
          <span class="grid h-11 w-11 place-items-center rounded-lg" :class="m.tone"><component :is="m.icon" class="h-5 w-5" /></span>
          <p class="mt-3 font-heading text-2xl font-bold">{{ m.value }}</p>
          <p class="text-sm text-muted">{{ m.label }}</p>
        </div>
      </div>

      <!-- Shortcuts -->
      <h3 class="mb-3 mt-8 font-heading text-lg font-semibold">{{ $t('dash.quickAccess') }}</h3>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <RouterLink v-for="s in shortcuts" :key="s.label" :to="s.to" class="card group flex items-center justify-between p-5 transition hover:shadow-pop">
          <div class="flex items-center gap-3">
            <span class="grid h-11 w-11 place-items-center rounded-lg bg-primary-50 text-primary-600"><component :is="s.icon" class="h-5 w-5" /></span>
            <div>
              <p class="font-heading font-semibold">{{ s.label }}</p>
              <p class="text-xs text-muted">{{ s.desc }}</p>
            </div>
          </div>
          <ArrowRight class="h-5 w-5 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-primary-600" />
        </RouterLink>
      </div>

      <!-- Recent orders + Low stock -->
      <div class="mt-8 grid gap-6 lg:grid-cols-2">
        <div class="card p-5">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="font-heading font-semibold">{{ $t('dash.recentOrders') }}</h3>
            <RouterLink :to="{ name: 'admin-orders' }" class="text-sm font-medium text-primary-600 hover:underline">
              {{ $t('dash.openOrders') }} <ArrowRight class="inline h-3.5 w-3.5 rtl:rotate-180" />
            </RouterLink>
          </div>
          <ul v-if="dash?.recent_orders?.length" class="divide-y divide-slate-100">
            <li v-for="o in dash.recent_orders" :key="o.number" class="flex items-center justify-between py-3">
              <div class="flex items-center gap-3">
                <span class="grid h-9 w-9 place-items-center rounded-lg bg-slate-100 text-slate-400"><Eye class="h-4 w-4" /></span>
                <div>
                  <p class="text-sm font-medium">#{{ o.number }}</p>
                  <p class="text-xs text-slate-400">{{ (o.created_at || '').slice(0, 10) }}</p>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <StatusBadge :status="o.status" />
                <span class="text-sm font-semibold">{{ o.total }} {{ o.currency }}</span>
              </div>
            </li>
          </ul>
          <EmptyState v-else :title="$t('dash.noRecentOrders')" :message="$t('dash.noRecentOrdersMsg')" />
        </div>

        <div class="card p-5">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="font-heading font-semibold">{{ $t('dash.needsRestock') }}</h3>
            <RouterLink :to="{ name: 'admin-inventory' }" class="text-sm font-medium text-primary-600 hover:underline">{{ $t('dash.inventory') }} <ArrowRight class="inline h-3.5 w-3.5 rtl:rotate-180" /></RouterLink>
          </div>
          <ul v-if="lowStock.length" class="space-y-2">
            <li v-for="s in lowStock" :key="s.id" class="flex items-center justify-between rounded-lg bg-lightbg px-3 py-2 text-sm">
              <span class="flex items-center gap-2"><AlertTriangle class="h-4 w-4 text-amber-500" /> {{ String(s.variant).slice(0, 8) }}</span>
              <span class="font-medium" :class="s.is_out_of_stock ? 'text-secondary-500' : 'text-amber-600'">{{ s.available_quantity }} {{ $t('dash.left') }}</span>
            </li>
          </ul>
          <EmptyState v-else :title="$t('dash.stockHealthy')" :message="$t('dash.needRestockMsg')" />
        </div>
      </div>
    </template>
  </div>
</template>
