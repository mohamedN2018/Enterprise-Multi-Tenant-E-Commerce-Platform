<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  Store as StoreIcon,
  Package,
  Tags,
  DollarSign,
  ShieldAlert,
  ExternalLink,
  Settings2,
  Eye,
  Users
} from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import DataTable from '@/components/ui/DataTable.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useTenantStore } from '@/stores/tenant';
import { storefront } from '@/services/storefront';
import http from '@/services/http';

const router = useRouter();
const tenant = useTenantStore();

const loading = ref(true);
const allStores = ref([]);
const stats = ref({ stores: 0, products: 0, categories: 0 });
const rollup = ref({ revenue: 0, orders: 0, currency: 'USD' });

const manageableIds = computed(() => new Set(tenant.stores.map((s) => s.id)));

const columns = [
  { key: 'name', label: 'Store' },
  { key: 'country', label: 'Country' },
  { key: 'currency', label: 'Currency' },
  { key: 'actions', label: '', align: 'right' }
];

const kpis = computed(() => [
  { label: 'Total stores', value: stats.value.stores, icon: StoreIcon, tone: 'text-primary-600 bg-primary-50' },
  { label: 'Total products', value: stats.value.products, icon: Package, tone: 'text-sky-600 bg-sky-50' },
  { label: 'Categories', value: stats.value.categories, icon: Tags, tone: 'text-violet-600 bg-violet-50' },
  { label: 'My stores', value: tenant.stores.length, icon: Users, tone: 'text-emerald-600 bg-emerald-50' }
]);

const viewStorefront = (s) => router.push({ name: 'products', query: { store: s.slug } });
const manage = (s) => {
  tenant.select(s.id);
  router.push({ name: 'admin-dashboard' });
};

const load = async () => {
  loading.value = true;
  try {
    await tenant.ensureReady();
    const [st, pr, cat] = await Promise.all([
      storefront.stores({ page_size: 100 }),
      storefront.products({ page_size: 1 }),
      storefront.categories()
    ]);
    allStores.value = st.data?.results || st.data || [];
    stats.value = {
      stores: st.$meta?.pagination?.count ?? allStores.value.length,
      products: pr.$meta?.pagination?.count ?? 0,
      categories: (cat.data || []).length
    };

    // Roll up revenue/orders across the stores this admin can actually manage.
    const results = await Promise.allSettled(
      tenant.stores.map((s) => http.get('/analytics/dashboard/', { headers: { 'X-Store-Id': s.id } }))
    );
    let revenue = 0;
    let orders = 0;
    results.forEach((r) => {
      if (r.status === 'fulfilled') {
        const d = r.value.data;
        revenue += Number(d?.orders?.revenue || 0);
        orders += Number(d?.orders?.count || 0);
      }
    });
    rollup.value = { revenue: revenue.toFixed(2), orders, currency: tenant.currency };
  } finally {
    loading.value = false;
  }
};

onMounted(load);
</script>

<template>
  <div>
    <div v-if="loading" class="flex min-h-[50vh] items-center justify-center"><Spinner :size="30" label="Loading platform…" /></div>

    <EmptyState
      v-else-if="!tenant.isPlatform"
      :icon="ShieldAlert"
      title="Platform admins only"
      message="This area is restricted to super-administrators."
    >
      <RouterLink :to="{ name: 'admin-dashboard' }" class="btn btn-primary btn-sm">Back to dashboard</RouterLink>
    </EmptyState>

    <template v-else>
      <PageHeader title="Platform overview" subtitle="Marketplace-wide view for super-administrators.">
        <template #actions>
          <a href="/django-admin/" target="_blank" rel="noopener" class="btn btn-outline btn-sm">
            <ExternalLink class="h-4 w-4" /> Django admin
          </a>
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

      <!-- Rollup across manageable stores -->
      <div class="mt-6 grid gap-4 sm:grid-cols-2">
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-emerald-50 text-emerald-600"><DollarSign class="h-6 w-6" /></span>
          <div>
            <p class="font-heading text-2xl font-bold">{{ rollup.revenue }} {{ rollup.currency }}</p>
            <p class="text-sm text-muted">Revenue across my {{ tenant.stores.length }} store(s)</p>
          </div>
        </div>
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-sky-50 text-sky-600"><Package class="h-6 w-6" /></span>
          <div>
            <p class="font-heading text-2xl font-bold">{{ rollup.orders }}</p>
            <p class="text-sm text-muted">Orders across my stores</p>
          </div>
        </div>
      </div>

      <!-- All stores -->
      <div class="mt-8">
        <h2 class="section-title mb-4 text-xl">All stores on the platform</h2>
        <DataTable :columns="columns" :rows="allStores" empty-title="No stores" empty-message="No active stores on the marketplace yet.">
          <template #cell-name="{ row }">
            <div class="flex items-center gap-3">
              <span class="grid h-9 w-9 place-items-center rounded-lg bg-primary-50 text-primary-600"><StoreIcon class="h-4 w-4" /></span>
              <div>
                <p class="font-medium text-ink">{{ row.name }}</p>
                <p class="text-xs text-muted">{{ row.slug }}</p>
              </div>
            </div>
          </template>
          <template #cell-country="{ value }">{{ value || '—' }}</template>
          <template #cell-actions="{ row }">
            <div class="flex justify-end gap-2">
              <button class="btn btn-ghost btn-sm" @click="viewStorefront(row)"><Eye class="h-4 w-4" /> View</button>
              <button v-if="manageableIds.has(row.id)" class="btn btn-outline btn-sm" @click="manage(row)"><Settings2 class="h-4 w-4" /> Manage</button>
              <StatusBadge v-else status="gray" label="Not a member" />
            </div>
          </template>
        </DataTable>
        <p class="mt-3 text-xs text-muted">
          Management is limited to stores you belong to. Use the Django admin for platform-wide user &amp; store administration.
        </p>
      </div>
    </template>
  </div>
</template>
