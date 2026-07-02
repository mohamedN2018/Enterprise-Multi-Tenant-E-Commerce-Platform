<script setup>
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { MapPin, BadgeCheck, Package } from 'lucide-vue-next';
import ProductCard from '@/components/ProductCard.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Pagination from '@/components/ui/Pagination.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { storefront } from '@/services/storefront';
import { usePaginated } from '@/composables/usePaginated';
import { useAddToCart } from '@/composables/useAddToCart';
import { storeBanner, storeLogo, onImgError } from '@/utils/media';

const route = useRoute();
const { add, adding } = useAddToCart();

const store = ref(null);
const loadingStore = ref(true);
const notFound = ref(false);

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  storefront.storeProducts(route.params.slug, params)
);

const changePage = (n) => {
  page.value = n;
  load();
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

const loadStore = async (slug) => {
  loadingStore.value = true;
  notFound.value = false;
  page.value = 1;
  try {
    const res = await storefront.store(slug);
    store.value = res.data;
    await load();
  } catch {
    notFound.value = true;
  } finally {
    loadingStore.value = false;
  }
};

watch(() => route.params.slug, (slug) => slug && loadStore(slug), { immediate: true });
</script>

<template>
  <div>
    <div v-if="loadingStore" class="flex min-h-[50vh] items-center justify-center"><Spinner :size="30" label="Loading store…" /></div>

    <div v-else-if="notFound || !store" class="container py-16">
      <EmptyState title="Store not found" message="This store may no longer be available.">
        <RouterLink :to="{ name: 'stores' }" class="btn btn-primary btn-sm">Browse stores</RouterLink>
      </EmptyState>
    </div>

    <template v-else>
      <!-- Banner -->
      <section class="relative">
        <div class="h-52 w-full overflow-hidden bg-lightbg sm:h-64">
          <img :src="storeBanner(store, 1600, 400)" alt="" class="h-full w-full object-cover" @error="onImgError" />
          <div class="absolute inset-0 bg-ink/30"></div>
        </div>
        <div class="container relative -mt-16">
          <div class="flex flex-col items-start gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-card sm:flex-row sm:items-center">
            <img :src="storeLogo(store, 96)" :alt="store.name" class="h-20 w-20 rounded-xl border-2 border-white object-cover shadow" @error="onImgError" />
            <div class="min-w-0 flex-1">
              <h1 class="flex items-center gap-2 font-heading text-2xl font-black text-ink">
                {{ store.name }}
                <BadgeCheck class="h-5 w-5 text-primary-600" />
              </h1>
              <p v-if="store.country" class="flex items-center gap-1 text-sm text-muted"><MapPin class="h-4 w-4" /> {{ store.country }} · {{ store.currency }}</p>
            </div>
            <div class="text-sm text-muted"><span class="font-semibold text-ink">{{ total }}</span> products</div>
          </div>
          <p v-if="store.description" class="mt-4 max-w-3xl text-muted">{{ store.description }}</p>
        </div>
      </section>

      <!-- Products -->
      <section class="container py-10">
        <h2 class="section-title mb-6">Products</h2>
        <div v-if="loading" class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
          <div v-for="n in 8" :key="n" class="rounded-xl border border-slate-200"><div class="skeleton aspect-[4/3] rounded-t-xl"></div><div class="space-y-2 p-4"><div class="skeleton mx-auto h-4 w-2/3 rounded"></div><div class="skeleton mx-auto h-4 w-1/3 rounded"></div></div></div>
        </div>
        <template v-else-if="items.length">
          <div class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
            <ProductCard v-for="p in items" :key="p.id" :product="p" :adding="adding === p.id" @add="add" />
          </div>
          <div v-if="totalPages > 1" class="mt-10"><Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" /></div>
        </template>
        <EmptyState v-else :icon="Package" title="No products yet" message="This store hasn't published any products yet." />
      </section>
    </template>
  </div>
</template>
