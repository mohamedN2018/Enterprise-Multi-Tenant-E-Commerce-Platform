<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Search, SlidersHorizontal, X } from 'lucide-vue-next';
import ProductCard from '@/components/ProductCard.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Pagination from '@/components/ui/Pagination.vue';
import Breadcrumbs from '@/components/ui/Breadcrumbs.vue';
import { storefront } from '@/services/storefront';
import { usePaginated } from '@/composables/usePaginated';
import { useAddToCart } from '@/composables/useAddToCart';

const route = useRoute();
const router = useRouter();
const { add, adding } = useAddToCart();

const categories = ref([]);
const term = ref(route.query.search || '');
const mobileFilters = ref(false);

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  storefront.products(params)
);

const activeCategory = computed(() => route.query.category || '');
const activeStore = computed(() => route.query.store || '');
const onSale = computed(() => route.query.on_sale === '1');

const queryParams = () => {
  const p = {};
  if (route.query.search) p.search = route.query.search;
  if (route.query.category) p.category = route.query.category;
  if (route.query.store) p.store = route.query.store;
  if (route.query.on_sale) p.on_sale = 1;
  return p;
};

const fetch = () => load(queryParams());

const setQuery = (patch) => {
  const q = { ...route.query, ...patch };
  Object.keys(q).forEach((k) => (q[k] === '' || q[k] == null) && delete q[k]);
  page.value = 1;
  router.push({ query: q });
};

const submitSearch = () => setQuery({ search: term.value.trim() || undefined });
const toggleCategory = (name) => setQuery({ category: activeCategory.value === name ? undefined : name });
const toggleSale = () => setQuery({ on_sale: onSale.value ? undefined : '1' });
const clearAll = () => {
  term.value = '';
  router.push({ query: {} });
};

const changePage = (n) => {
  page.value = n;
  fetch();
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

watch(
  () => route.query,
  () => {
    term.value = route.query.search || '';
    page.value = 1;
    fetch();
  }
);

onMounted(async () => {
  const cat = await storefront.categories();
  categories.value = cat.data || [];
  fetch();
});
</script>

<template>
  <div class="container py-8">
    <Breadcrumbs :items="[{ label: 'Home', to: { name: 'home' } }, { label: 'Products' }]" />
    <div class="mt-3 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold">
          {{ activeStore ? `Store: ${activeStore}` : activeCategory || 'All products' }}
        </h1>
        <p class="text-sm text-slate-500">{{ total }} products found</p>
      </div>
      <form class="relative w-full max-w-sm" @submit.prevent="submitSearch">
        <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input v-model="term" type="search" placeholder="Search products…" class="input pl-9" />
      </form>
    </div>

    <div class="mt-6 flex items-center gap-3 lg:hidden">
      <button class="btn btn-outline btn-sm" @click="mobileFilters = !mobileFilters">
        <SlidersHorizontal class="h-4 w-4" /> Filters
      </button>
      <button v-if="activeCategory || onSale || activeStore || route.query.search" class="btn btn-ghost btn-sm" @click="clearAll">
        <X class="h-4 w-4" /> Clear
      </button>
    </div>

    <div class="mt-6 grid gap-8 lg:grid-cols-[220px_1fr]">
      <!-- Filters -->
      <aside :class="mobileFilters ? 'block' : 'hidden'" class="lg:block">
        <div class="card space-y-5 p-4">
          <div>
            <div class="mb-2 flex items-center justify-between">
              <h3 class="text-sm font-semibold">Filters</h3>
              <button v-if="activeCategory || onSale || activeStore || route.query.search" class="text-xs text-primary-600 hover:underline" @click="clearAll">
                Reset
              </button>
            </div>
            <label class="flex cursor-pointer items-center gap-2 text-sm">
              <input type="checkbox" :checked="onSale" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" @change="toggleSale" />
              On sale only
            </label>
          </div>
          <div>
            <h4 class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Categories</h4>
            <ul class="space-y-1">
              <li v-for="c in categories" :key="c.name">
                <button
                  class="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-sm hover:bg-slate-100"
                  :class="activeCategory === c.name ? 'bg-primary-50 font-medium text-primary-700' : 'text-slate-600'"
                  @click="toggleCategory(c.name)"
                >
                  <span>{{ c.name }}</span>
                  <span class="text-xs text-slate-400">{{ c.product_count }}</span>
                </button>
              </li>
            </ul>
          </div>
        </div>
      </aside>

      <!-- Grid -->
      <div>
        <div v-if="loading" class="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <div v-for="n in 9" :key="n" class="card overflow-hidden">
            <div class="skeleton aspect-[4/3]"></div>
            <div class="space-y-2 p-4">
              <div class="skeleton h-4 w-3/4 rounded"></div>
              <div class="skeleton h-4 w-1/2 rounded"></div>
            </div>
          </div>
        </div>

        <template v-else-if="items.length">
          <div class="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <ProductCard v-for="p in items" :key="p.id" :product="p" :adding="adding === p.id" @add="add" />
          </div>
          <div v-if="totalPages > 1" class="mt-8">
            <Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" />
          </div>
        </template>

        <EmptyState v-else title="No products found" message="Try adjusting your filters or search terms.">
          <button class="btn btn-primary btn-sm" @click="clearAll">Clear filters</button>
        </EmptyState>
      </div>
    </div>
  </div>
</template>
