<script setup>
import { onMounted } from 'vue';
import { MapPin, ArrowRight } from 'lucide-vue-next';
import Breadcrumbs from '@/components/ui/Breadcrumbs.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Pagination from '@/components/ui/Pagination.vue';
import { storefront } from '@/services/storefront';
import { usePaginated } from '@/composables/usePaginated';
import { storeLogo, storeBanner, onImgError } from '@/utils/media';

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  storefront.stores(params)
);

const changePage = (n) => {
  page.value = n;
  load();
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

onMounted(() => load());
</script>

<template>
  <div class="container py-8">
    <Breadcrumbs :items="[{ label: 'Home', to: { name: 'home' } }, { label: 'Stores' }]" />
    <div class="mt-3 mb-6">
      <h1 class="text-2xl font-bold">Browse stores</h1>
      <p class="text-sm text-slate-500">{{ total }} independent stores on the marketplace</p>
    </div>

    <div v-if="loading" class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      <div v-for="n in 6" :key="n" class="card overflow-hidden">
        <div class="skeleton h-28"></div>
        <div class="space-y-2 p-4">
          <div class="skeleton h-4 w-1/2 rounded"></div>
          <div class="skeleton h-3 w-3/4 rounded"></div>
        </div>
      </div>
    </div>

    <template v-else-if="items.length">
      <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <RouterLink
          v-for="s in items"
          :key="s.id"
          :to="{ name: 'products', query: { store: s.slug } }"
          class="card group overflow-hidden transition hover:-translate-y-0.5 hover:shadow-pop"
        >
          <div class="h-28 overflow-hidden bg-slate-100">
            <img :src="storeBanner(s)" alt="" class="h-full w-full object-cover transition group-hover:scale-105" @error="onImgError" />
          </div>
          <div class="p-4">
            <div class="flex items-start gap-3">
              <img :src="storeLogo(s)" :alt="s.name" class="h-14 w-14 -mt-10 rounded-xl border-2 border-white object-cover shadow" @error="onImgError" />
              <div class="min-w-0 flex-1 pt-1">
                <p class="truncate font-semibold group-hover:text-primary-700">{{ s.name }}</p>
                <p v-if="s.country" class="flex items-center gap-1 text-xs text-slate-400">
                  <MapPin class="h-3 w-3" /> {{ s.country }}
                </p>
              </div>
            </div>
            <p class="clamp-2 mt-3 text-sm text-slate-500">{{ s.description || 'A curated independent store.' }}</p>
            <span class="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary-600">
              Visit store <ArrowRight class="h-4 w-4 transition group-hover:translate-x-0.5" />
            </span>
          </div>
        </RouterLink>
      </div>
      <div v-if="totalPages > 1" class="mt-8">
        <Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" />
      </div>
    </template>

    <EmptyState v-else title="No stores yet" message="Check back soon — new sellers are joining regularly." />
  </div>
</template>
