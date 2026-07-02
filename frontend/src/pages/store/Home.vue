<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, Sparkles, Tag, Store as StoreIcon, ShieldCheck, Truck, RotateCcw } from 'lucide-vue-next';
import ProductCard from '@/components/ProductCard.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { storefront } from '@/services/storefront';
import { useAddToCart } from '@/composables/useAddToCart';
import { heroImage, catImage, storeLogo, storeBanner, onImgError } from '@/utils/media';

const router = useRouter();
const { add, adding } = useAddToCart();

const categories = ref([]);
const stores = ref([]);
const newest = ref([]);
const deals = ref([]);
const loading = ref(true);

const perks = [
  { icon: Truck, title: 'Fast delivery', text: 'Reliable shipping from every store' },
  { icon: ShieldCheck, title: 'Secure checkout', text: 'Protected payments end to end' },
  { icon: RotateCcw, title: 'Easy returns', text: 'Hassle-free within 30 days' }
];

const goCategory = (name) => router.push({ name: 'products', query: { category: name } });

onMounted(async () => {
  try {
    const [cat, st, nw, dl] = await Promise.all([
      storefront.categories(),
      storefront.stores({ page_size: 8 }),
      storefront.products({ page_size: 8 }),
      storefront.products({ on_sale: 1, page_size: 8 })
    ]);
    categories.value = (cat.data || []).slice(0, 8);
    stores.value = (st.data?.results || st.data || []).slice(0, 6);
    newest.value = nw.data?.results || nw.data || [];
    deals.value = dl.data?.results || dl.data || [];
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="relative overflow-hidden bg-ink text-white">
      <img
        :src="heroImage('landing', 1600, 560)"
        alt=""
        class="absolute inset-0 h-full w-full object-cover opacity-30"
        @error="onImgError"
      />
      <div class="absolute inset-0 bg-gradient-to-r from-ink via-ink/80 to-transparent"></div>
      <div class="container relative py-20 lg:py-28">
        <span class="chip border-white/20 bg-white/10 text-white">
          <Sparkles class="h-3.5 w-3.5" /> Thousands of products, one marketplace
        </span>
        <h1 class="mt-4 max-w-2xl text-4xl font-bold leading-tight lg:text-5xl">
          Discover independent stores you'll love.
        </h1>
        <p class="mt-4 max-w-xl text-lg text-slate-200">
          Shop curated products from verified sellers — fashion, tech, home and more, all in one place.
        </p>
        <div class="mt-8 flex flex-wrap gap-3">
          <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-lg">
            Shop all products <ArrowRight class="h-4 w-4" />
          </RouterLink>
          <RouterLink :to="{ name: 'stores' }" class="btn btn-light btn-lg">Browse stores</RouterLink>
        </div>
      </div>
    </section>

    <!-- Perks -->
    <section class="border-b border-slate-200 bg-white">
      <div class="container grid gap-6 py-6 sm:grid-cols-3">
        <div v-for="p in perks" :key="p.title" class="flex items-center gap-3">
          <span class="grid h-11 w-11 place-items-center rounded-xl bg-primary-50 text-primary-600">
            <component :is="p.icon" class="h-5 w-5" />
          </span>
          <div>
            <p class="text-sm font-semibold">{{ p.title }}</p>
            <p class="text-xs text-slate-500">{{ p.text }}</p>
          </div>
        </div>
      </div>
    </section>

    <div class="container space-y-14 py-12">
      <!-- Categories -->
      <section v-if="categories.length">
        <div class="mb-5 flex items-end justify-between">
          <h2 class="section-title">Shop by category</h2>
          <RouterLink :to="{ name: 'products' }" class="text-sm font-medium text-primary-600 hover:underline">
            View all
          </RouterLink>
        </div>
        <div class="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-8">
          <button
            v-for="c in categories"
            :key="c.name"
            class="group flex flex-col items-center gap-2"
            @click="goCategory(c.name)"
          >
            <span class="relative h-20 w-20 overflow-hidden rounded-full ring-2 ring-transparent transition group-hover:ring-primary-400">
              <img :src="catImage(c.name)" :alt="c.name" class="h-full w-full object-cover" @error="onImgError" />
            </span>
            <span class="text-center text-xs font-medium text-slate-700">{{ c.name }}</span>
            <span class="text-[11px] text-slate-400">{{ c.product_count }} items</span>
          </button>
        </div>
      </section>

      <!-- Featured stores -->
      <section v-if="stores.length">
        <div class="mb-5 flex items-end justify-between">
          <h2 class="section-title">Featured stores</h2>
          <RouterLink :to="{ name: 'stores' }" class="text-sm font-medium text-primary-600 hover:underline">
            All stores
          </RouterLink>
        </div>
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <RouterLink
            v-for="s in stores"
            :key="s.id"
            :to="{ name: 'products', query: { store: s.slug } }"
            class="card group overflow-hidden"
          >
            <div class="h-24 overflow-hidden bg-slate-100">
              <img :src="storeBanner(s)" alt="" class="h-full w-full object-cover transition group-hover:scale-105" @error="onImgError" />
            </div>
            <div class="flex items-center gap-3 p-4">
              <img :src="storeLogo(s)" :alt="s.name" class="h-12 w-12 -mt-8 rounded-xl border-2 border-white object-cover shadow" @error="onImgError" />
              <div class="min-w-0">
                <p class="truncate font-semibold group-hover:text-primary-700">{{ s.name }}</p>
                <p class="clamp-1 text-xs text-slate-500">{{ s.description || 'Independent store' }}</p>
              </div>
            </div>
          </RouterLink>
        </div>
      </section>

      <!-- Deals -->
      <section v-if="deals.length">
        <div class="mb-5 flex items-end justify-between">
          <h2 class="section-title flex items-center gap-2">
            <Tag class="h-5 w-5 text-rose-500" /> Today's deals
          </h2>
          <RouterLink :to="{ name: 'products', query: { on_sale: 1 } }" class="text-sm font-medium text-primary-600 hover:underline">
            More deals
          </RouterLink>
        </div>
        <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          <ProductCard
            v-for="p in deals"
            :key="p.id"
            :product="p"
            :adding="adding === p.id"
            @add="add"
          />
        </div>
      </section>

      <!-- New arrivals -->
      <section>
        <div class="mb-5 flex items-end justify-between">
          <h2 class="section-title">New arrivals</h2>
          <RouterLink :to="{ name: 'products' }" class="text-sm font-medium text-primary-600 hover:underline">
            Browse all
          </RouterLink>
        </div>
        <div v-if="loading" class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          <div v-for="n in 8" :key="n" class="card overflow-hidden">
            <div class="skeleton aspect-[4/3]"></div>
            <div class="space-y-2 p-4">
              <div class="skeleton h-4 w-3/4 rounded"></div>
              <div class="skeleton h-4 w-1/2 rounded"></div>
            </div>
          </div>
        </div>
        <div v-else-if="newest.length" class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          <ProductCard
            v-for="p in newest"
            :key="p.id"
            :product="p"
            :adding="adding === p.id"
            @add="add"
          />
        </div>
        <EmptyState v-else :icon="StoreIcon" title="No products yet" message="Check back soon for new arrivals." />
      </section>
    </div>
  </div>
</template>
