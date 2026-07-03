<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Search, SlidersHorizontal, X } from 'lucide-vue-next';
import ProductCard from '@/components/ProductCard.vue';
import ProductCarousel from '@/components/ProductCarousel.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Pagination from '@/components/ui/Pagination.vue';
import PageHero from '@/components/ui/PageHero.vue';
import { storefront } from '@/services/storefront';
import { usePaginated } from '@/composables/usePaginated';
import { useAddToCart } from '@/composables/useAddToCart';

const route = useRoute();
const router = useRouter();
const { add, adding } = useAddToCart();

const categories = ref([]);
const recommended = ref([]);
const term = ref(route.query.search || '');
const mobileFilters = ref(false);

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  storefront.products(params)
);

const activeCategory = computed(() => route.query.category || '');
const activeStore = computed(() => route.query.store || '');
const onSale = computed(() => route.query.on_sale === '1');
const hasFilters = computed(() => activeCategory.value || onSale.value || activeStore.value || route.query.search);

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

const heading = computed(() => (activeStore.value ? activeStore.value : activeCategory.value || 'All Products'));

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
  try {
    const r = await storefront.products({ page_size: 16 });
    recommended.value = r.data?.results || r.data || [];
  } catch {
    recommended.value = [];
  }
});
</script>

<template>
  <div>
    <PageHero :title="$t('shop.title')" :items="[{ label: $t('shop.title') }]" />

    <div class="container py-10">
      <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 class="section-title capitalize">{{ heading }}</h2>
          <p class="text-sm text-muted">{{ total }} {{ $t('shop.productsFound') }}</p>
        </div>
        <form class="relative w-full max-w-sm" @submit.prevent="submitSearch">
          <Search class="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input v-model="term" type="search" :placeholder="$t('nav.searchPlaceholder')" class="input rounded-full ps-9" />
        </form>
      </div>

      <div class="mb-4 flex items-center gap-3 lg:hidden">
        <button class="btn btn-outline btn-sm" @click="mobileFilters = !mobileFilters"><SlidersHorizontal class="h-4 w-4" /> {{ $t('shop.filter') }}</button>
        <button v-if="hasFilters" class="btn btn-ghost btn-sm" @click="clearAll"><X class="h-4 w-4" /> {{ $t('common.clear') }}</button>
      </div>

      <div class="grid gap-8 lg:grid-cols-[260px_1fr]">
        <!-- Sidebar -->
        <aside :class="mobileFilters ? 'block' : 'hidden'" class="lg:block">
          <div class="space-y-6">
            <div class="rounded-xl border border-slate-200 p-5">
              <h3 class="mb-3 border-b border-slate-100 pb-2 font-heading text-lg font-bold text-ink">{{ $t('shop.categories') }}</h3>
              <ul>
                <li v-for="c in categories" :key="c.name" class="flex items-center justify-between border-b border-slate-50 py-2 last:border-0">
                  <button class="text-sm transition hover:text-primary-600" :class="activeCategory === c.name ? 'font-semibold text-primary-600' : 'text-ink'" @click="toggleCategory(c.name)">
                    {{ c.name }}
                  </button>
                  <span class="text-xs text-muted">({{ c.product_count }})</span>
                </li>
              </ul>
            </div>
            <div class="rounded-xl border border-slate-200 p-5">
              <h3 class="mb-3 border-b border-slate-100 pb-2 font-heading text-lg font-bold text-ink">{{ $t('shop.filter') }}</h3>
              <label class="flex cursor-pointer items-center gap-2 text-sm text-ink">
                <input type="checkbox" :checked="onSale" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" @change="toggleSale" />
                {{ $t('shop.onSaleOnly') }}
              </label>
              <button v-if="hasFilters" class="mt-4 text-sm text-primary-600 hover:underline" @click="clearAll">{{ $t('shop.resetFilters') }}</button>
            </div>
          </div>
        </aside>

        <!-- Grid -->
        <div>
          <div v-if="loading" class="grid grid-cols-2 gap-5 sm:grid-cols-3">
            <div v-for="n in 9" :key="n" class="rounded-xl border border-slate-200">
              <div class="skeleton aspect-[4/3] rounded-t-xl"></div>
              <div class="space-y-2 p-4"><div class="skeleton mx-auto h-4 w-2/3 rounded"></div><div class="skeleton mx-auto h-4 w-1/3 rounded"></div></div>
            </div>
          </div>

          <template v-else-if="items.length">
            <div class="grid grid-cols-2 gap-5 sm:grid-cols-3">
              <ProductCard v-for="p in items" :key="p.id" :product="p" :adding="adding === p.id" @add="add" />
            </div>
            <div v-if="totalPages > 1" class="mt-10">
              <Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" />
            </div>
          </template>

          <EmptyState v-else :title="$t('shop.noProducts')" :message="$t('shop.noProductsMsg')">
            <button class="btn btn-primary btn-sm" @click="clearAll">{{ $t('shop.clearFilters') }}</button>
          </EmptyState>
        </div>
      </div>

      <!-- Recommendations -->
      <div v-if="recommended.length" class="mt-14">
        <ProductCarousel :title="$t('rec.highlyRated')" :products="recommended" :adding-id="adding" @add="add" />
      </div>
    </div>
  </div>
</template>
