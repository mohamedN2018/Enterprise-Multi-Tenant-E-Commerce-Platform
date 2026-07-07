<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  ArrowRight,
  RotateCcw,
  Truck,
  Headphones,
  Lock,
  ShieldCheck,
  Sparkles,
  Store as StoreIcon,
  LayoutGrid,
  Quote,
  Rocket,
  Flame,
  ChevronLeft,
  Zap,
  HeartHandshake,
  CheckCircle2
} from 'lucide-vue-next';
import ProductCard from '@/components/ProductCard.vue';
import ProductCarousel from '@/components/ProductCarousel.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { storefront } from '@/services/storefront';
import { useAddToCart } from '@/composables/useAddToCart';
import { catImage, storeBanner, storeLogo, productImage, onImgError } from '@/utils/media';
import { getRecentlyViewed } from '@/utils/recent';
import { catName } from '@/utils/i18nData';
import { t } from '@/i18n';

const router = useRouter();
const { add, adding } = useAddToCart();

const categories = ref([]);
const stores = ref([]);
const newest = ref([]);
const deals = ref([]);
const pool = ref([]);
const productCount = ref(0);
const loading = ref(true);
const tab = ref('all');
const recent = ref(getRecentlyViewed());

// Amazon-style recommendation rails derived from the product pool.
const bestSellers = computed(() =>
  [...pool.value]
    .sort(
      (a, b) =>
        Number(b.rating ?? b.average_rating ?? 0) - Number(a.rating ?? a.average_rating ?? 0) ||
        Number(b.review_count ?? 0) - Number(a.review_count ?? 0)
    )
    .slice(0, 12)
);
const moreToConsider = computed(() => pool.value.slice(0, 12));
const alsoBought = computed(() => pool.value.slice(6, 18));
const heroBest = computed(() => bestSellers.value.slice(0, 4));
const topCategories = computed(() => categories.value.slice(0, 8));

const services = [
  { icon: Truck, key: 'freeShipping' },
  { icon: Lock, key: 'secure' },
  { icon: Headphones, key: 'support' },
  { icon: RotateCcw, key: 'freeReturn' }
];

// "Why q-shop" value props for the About section.
const values = [
  { icon: StoreIcon, key: 'curated' },
  { icon: ShieldCheck, key: 'secure' },
  { icon: Zap, key: 'fast' },
  { icon: HeartHandshake, key: 'protection' }
];

const shown = computed(() => (tab.value === 'deals' ? deals.value : newest.value).slice(0, 8));
const goCategory = (name) => router.push({ name: 'products', query: { category: name } });

const statItems = computed(() => [
  { value: `${stores.value.length || 10}+`, label: t('home.stores') },
  { value: `${productCount.value || pool.value.length || 100}+`, label: t('about.productsWord') },
  { value: `${categories.value.length || 10}+`, label: t('home.categories') },
  { value: '24/7', label: t('home.support') }
]);

onMounted(async () => {
  // allSettled: one failing/empty endpoint must not blank the whole page.
  const results = await Promise.allSettled([
    storefront.categories(),
    storefront.stores({ page_size: 6 }),
    // Home rails hide sold-out products so they don't take prime space.
    storefront.products({ page_size: 8, in_stock: 1 }),
    storefront.products({ on_sale: 1, page_size: 8, in_stock: 1 }),
    storefront.products({ page_size: 24, in_stock: 1 })
  ]);
  const val = (i) => (results[i].status === 'fulfilled' ? results[i].value : null);
  const list = (i) => {
    const d = val(i)?.data;
    return d?.results || (Array.isArray(d) ? d : []) || [];
  };
  const cat = val(0)?.data;
  categories.value = (Array.isArray(cat) ? cat : cat?.results || []).slice(0, 12);
  stores.value = list(1);
  newest.value = list(2);
  deals.value = list(3);
  pool.value = list(4);
  productCount.value = val(4)?.$meta?.pagination?.count || pool.value.length;
  loading.value = false;
});
</script>

<template>
  <div>
    <!-- ===== HERO ===== -->
    <section class="relative overflow-hidden bg-gradient-to-br from-[#0d1526] via-[#111c31] to-primary-900 text-white">
      <div class="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-primary-600/25 blur-3xl"></div>
      <div class="pointer-events-none absolute -bottom-32 left-1/4 h-80 w-80 rounded-full bg-secondary-500/20 blur-3xl"></div>

      <div class="container relative grid gap-6 pb-12 pt-10 lg:grid-cols-[240px_1fr] lg:pb-16 lg:pt-14">
        <!-- Categories quick-nav (desktop) -->
        <aside v-if="topCategories.length" class="hidden lg:block">
          <div class="overflow-hidden rounded-2xl border border-white/15 bg-white/5 backdrop-blur">
            <div class="flex items-center gap-2 border-b border-white/10 px-4 py-3 font-heading text-sm font-bold">
              <LayoutGrid class="h-4 w-4 text-primary-400" /> {{ $t('nav.allCategories') }}
            </div>
            <ul class="hero-scroll max-h-[380px] overflow-y-auto py-1">
              <li v-for="c in topCategories" :key="c.name">
                <button class="flex w-full items-center gap-3 px-4 py-2.5 text-start text-sm text-white/85 transition hover:bg-white/10 hover:text-white" @click="goCategory(c.name)">
                  <span class="h-8 w-8 shrink-0 overflow-hidden rounded-full ring-1 ring-white/20">
                    <img :src="catImage(c.name, 64)" :alt="c.name" class="h-full w-full object-cover" @error="onImgError" />
                  </span>
                  <span class="min-w-0 flex-1 truncate">{{ catName(c) }}</span>
                  <ChevronLeft class="h-4 w-4 shrink-0 text-white/40 rtl:rotate-180" />
                </button>
              </li>
            </ul>
          </div>
        </aside>

        <!-- Hero content -->
        <div class="grid items-center gap-8 lg:grid-cols-2">
          <div>
            <span class="chip border-white/20 bg-white/10 text-white"><Sparkles class="h-3.5 w-3.5 text-primary-400" /> {{ $t('home.heroBadge') }}</span>
            <h1 class="mt-5 font-heading text-4xl font-black leading-[1.1] lg:text-5xl">
              {{ $t('home.heroTitle') }} <span class="text-primary-400">{{ $t('home.heroHighlight') }}</span>
            </h1>
            <p class="mt-4 max-w-lg text-lg text-slate-300">{{ $t('home.heroSubtitle') }}</p>
            <div class="mt-8 flex flex-wrap gap-3">
              <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-lg">{{ $t('home.shopNow') }} <ArrowRight class="h-4 w-4 rtl:rotate-180" /></RouterLink>
              <RouterLink :to="{ name: 'seller-login' }" class="btn btn-light btn-lg"><Rocket class="h-4 w-4" /> {{ $t('home.becomeSeller') }}</RouterLink>
            </div>
            <!-- trust row -->
            <div class="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-300">
              <span class="flex items-center gap-1.5"><CheckCircle2 class="h-4 w-4 text-primary-400" /> {{ $t('home.svc.secure') }}</span>
              <span class="flex items-center gap-1.5"><CheckCircle2 class="h-4 w-4 text-primary-400" /> {{ $t('home.svc.freeShipping') }}</span>
              <span class="flex items-center gap-1.5"><CheckCircle2 class="h-4 w-4 text-primary-400" /> {{ $t('home.svc.freeReturn') }}</span>
            </div>
          </div>

          <!-- Best sellers showcase -->
          <div class="relative">
            <div class="absolute -inset-4 rounded-3xl bg-white/5 blur-xl"></div>
            <div class="relative rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur">
              <div class="mb-3 flex items-center justify-between">
                <p class="flex items-center gap-2 font-heading text-base font-bold"><Flame class="h-5 w-5 text-secondary-400" /> {{ $t('home.bestSellers') }}</p>
                <RouterLink :to="{ name: 'products' }" class="text-xs font-medium text-primary-300 hover:text-primary-200">{{ $t('home.viewAll') }}</RouterLink>
              </div>
              <div v-if="loading" class="space-y-2">
                <div v-for="n in 4" :key="n" class="skeleton h-16 rounded-xl"></div>
              </div>
              <div v-else-if="heroBest.length" class="space-y-2">
                <RouterLink
                  v-for="(p, i) in heroBest"
                  :key="p.id"
                  :to="{ name: 'product', params: { id: p.id } }"
                  class="flex items-center gap-3 rounded-xl bg-white/5 p-2 transition hover:bg-white/15"
                >
                  <span class="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-secondary-500 text-xs font-bold text-white">{{ i + 1 }}</span>
                  <img :src="productImage(p, 120, 120)" :alt="p.name" class="h-12 w-12 shrink-0 rounded-lg object-cover" @error="onImgError" />
                  <div class="min-w-0 flex-1">
                    <p class="clamp-1 text-sm font-medium text-white">{{ p.name }}</p>
                    <p class="clamp-1 text-xs text-white/60">{{ p.store_slug }}</p>
                  </div>
                  <span class="shrink-0 font-heading text-sm font-bold text-primary-300">{{ p.price }} {{ p.currency }}</span>
                </RouterLink>
              </div>
              <div v-else class="flex flex-col items-center gap-3 px-4 py-8 text-center">
                <span class="grid h-12 w-12 place-items-center rounded-full bg-white/10"><Flame class="h-6 w-6 text-secondary-400" /></span>
                <p class="text-sm font-medium text-white/80">{{ $t('home.noProductsYet') }}</p>
                <p class="text-xs text-white/50">{{ $t('home.noProductsYetMsg') }}</p>
                <RouterLink :to="{ name: 'products' }" class="btn btn-light btn-sm mt-1">{{ $t('home.viewAll') }}</RouterLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== SERVICES STRIP ===== -->
    <section class="border-b border-slate-200 bg-white dark:border-slate-800">
      <div class="container grid grid-cols-2 gap-px lg:grid-cols-4">
        <div v-for="s in services" :key="s.key" class="flex items-center gap-4 px-2 py-6">
          <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-primary-50 text-primary-600 dark:bg-primary-600/10">
            <component :is="s.icon" class="h-6 w-6" />
          </span>
          <div>
            <h6 class="font-heading text-sm font-bold text-ink">{{ $t('home.svc.' + s.key) }}</h6>
            <p class="text-xs text-muted">{{ $t('home.svc.' + s.key + 'Msg') }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== SHOP BY CATEGORY ===== -->
    <section v-if="topCategories.length" class="container py-14">
      <div class="mb-8 flex items-end justify-between">
        <div>
          <h2 class="section-title text-2xl lg:text-3xl">{{ $t('home.shopByCategory') }}</h2>
          <p class="mt-1 text-sm text-muted">{{ $t('home.categoriesSubtitle') }}</p>
        </div>
        <RouterLink :to="{ name: 'products' }" class="hidden text-sm font-medium text-primary-600 hover:underline sm:inline">{{ $t('home.viewAll') }}</RouterLink>
      </div>
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <button
          v-for="c in topCategories"
          :key="c.name"
          class="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white text-start transition hover:-translate-y-0.5 hover:border-primary-300 hover:shadow-pop dark:border-slate-700"
          @click="goCategory(c.name)"
        >
          <div class="aspect-[16/10] overflow-hidden bg-lightbg">
            <img :src="catImage(c.name, 320)" :alt="c.name" class="h-full w-full object-cover transition duration-500 group-hover:scale-110" @error="onImgError" />
          </div>
          <div class="flex items-center justify-between gap-2 p-4">
            <div class="min-w-0">
              <p class="truncate font-heading font-bold text-ink group-hover:text-primary-600">{{ catName(c) }}</p>
              <p class="text-xs text-muted">{{ c.product_count }} {{ $t('home.items') }}</p>
            </div>
            <span class="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary-50 text-primary-600 transition group-hover:bg-primary-600 group-hover:text-white dark:bg-primary-600/10">
              <ChevronLeft class="h-4 w-4 rtl:rotate-180" />
            </span>
          </div>
        </button>
      </div>
    </section>

    <!-- ===== PROMO BANNERS ===== -->
    <section class="container grid gap-4 pb-4 lg:grid-cols-2">
      <RouterLink :to="{ name: 'products', query: { on_sale: 1 } }" class="group relative flex items-center justify-between overflow-hidden rounded-2xl bg-gradient-to-br from-primary-600 to-primary-800 p-8 text-white transition hover:shadow-pop">
        <div class="relative z-10">
          <p class="mb-1 text-sm text-white/80">{{ $t('home.promo.dealsKicker') }}</p>
          <h3 class="font-heading text-2xl font-black">{{ $t('home.promo.dealsTitle') }}</h3>
          <span class="mt-4 inline-flex items-center gap-1 text-sm font-semibold">{{ $t('home.shopNow') }} <ArrowRight class="h-4 w-4 rtl:rotate-180" /></span>
        </div>
        <span class="absolute -bottom-6 -left-6 font-heading text-8xl font-black text-white/10 rtl:-right-6 rtl:left-auto">40%</span>
      </RouterLink>
      <RouterLink :to="{ name: 'stores' }" class="group relative flex items-center justify-between overflow-hidden rounded-2xl bg-gradient-to-br from-secondary-500 to-secondary-700 p-8 text-white transition hover:shadow-pop">
        <div class="relative z-10">
          <p class="mb-1 text-sm text-white/80">{{ $t('home.promo.storesKicker') }}</p>
          <h3 class="font-heading text-2xl font-black">{{ $t('home.promo.storesTitle') }}</h3>
          <span class="mt-4 inline-flex items-center gap-1 text-sm font-semibold">{{ $t('home.viewAll') }} <ArrowRight class="h-4 w-4 rtl:rotate-180" /></span>
        </div>
        <StoreIcon class="absolute -bottom-4 -left-4 h-28 w-28 text-white/10 rtl:-right-4 rtl:left-auto" />
      </RouterLink>
    </section>

    <!-- ===== PRODUCTS (new / on sale) ===== -->
    <section class="container py-10">
      <div class="mb-8 flex flex-col items-center justify-between gap-4 sm:flex-row">
        <h2 class="section-title text-2xl lg:text-3xl">{{ $t('home.ourProducts') }}</h2>
        <div class="flex gap-2">
          <button class="rounded-full px-5 py-2 text-sm font-medium transition" :class="tab === 'all' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100 dark:hover:bg-slate-700'" @click="tab = 'all'">{{ $t('home.newArrivals') }}</button>
          <button class="rounded-full px-5 py-2 text-sm font-medium transition" :class="tab === 'deals' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100 dark:hover:bg-slate-700'" @click="tab = 'deals'">{{ $t('home.onSale') }}</button>
        </div>
      </div>

      <div v-if="loading" class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
        <div v-for="n in 8" :key="n" class="rounded-xl border border-slate-200 dark:border-slate-700">
          <div class="skeleton aspect-[4/3] rounded-t-xl"></div>
          <div class="space-y-2 p-4"><div class="skeleton mx-auto h-4 w-2/3 rounded"></div><div class="skeleton mx-auto h-4 w-1/3 rounded"></div></div>
        </div>
      </div>
      <div v-else-if="shown.length" class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
        <ProductCard v-for="p in shown" :key="p.id" :product="p" :adding="adding === p.id" @add="add" />
      </div>
      <EmptyState v-else :title="$t('shop.noProducts')" :message="$t('home.noProductsYetMsg')" />

      <div class="mt-10 text-center">
        <RouterLink :to="{ name: 'products' }" class="btn btn-outline btn-lg">{{ $t('home.viewAllProducts') }} <ArrowRight class="h-4 w-4 rtl:rotate-180" /></RouterLink>
      </div>
    </section>

    <!-- ===== RECOMMENDATION RAILS ===== -->
    <div v-if="moreToConsider.length" class="container space-y-10 py-4">
      <ProductCarousel :title="$t('rec.moreToConsider')" :products="moreToConsider" :adding-id="adding" @add="add" />
      <ProductCarousel v-if="bestSellers.length" :title="$t('rec.bestSellers')" :products="bestSellers" :adding-id="adding" @add="add" />
      <ProductCarousel v-if="alsoBought.length" :title="$t('rec.alsoBought')" :products="alsoBought" :adding-id="adding" @add="add" />
    </div>

    <!-- ===== RECENTLY VIEWED ===== -->
    <section v-if="recent.length" class="container py-8">
      <h2 class="section-title mb-6">{{ $t('home.recentlyViewed') }}</h2>
      <div class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
        <ProductCard v-for="p in recent" :key="p.id" :product="p" :adding="adding === p.id" @add="add" />
      </div>
    </section>

    <!-- ===== FEATURED STORES ===== -->
    <section v-if="stores.length" class="border-y border-slate-200 bg-lightbg py-14 dark:border-slate-800">
      <div class="container">
        <div class="mb-6 flex items-end justify-between">
          <h2 class="section-title text-2xl lg:text-3xl">{{ $t('home.featuredStores') }}</h2>
          <RouterLink :to="{ name: 'stores' }" class="text-sm font-medium text-primary-600 hover:underline">{{ $t('home.viewAll') }}</RouterLink>
        </div>
        <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <RouterLink v-for="s in stores" :key="s.id" :to="{ name: 'store', params: { slug: s.slug } }" class="card group overflow-hidden transition hover:-translate-y-0.5 hover:shadow-pop">
            <div class="h-24 overflow-hidden bg-lightbg"><img :src="storeBanner(s)" alt="" class="h-full w-full object-cover transition group-hover:scale-105" @error="onImgError" /></div>
            <div class="flex items-center gap-3 p-4">
              <img :src="storeLogo(s)" :alt="s.name" class="-mt-8 h-12 w-12 rounded-xl border-2 border-white object-cover shadow dark:border-slate-800" @error="onImgError" />
              <div class="min-w-0">
                <p class="truncate font-heading font-semibold group-hover:text-primary-600">{{ s.name }}</p>
                <p class="clamp-1 text-xs text-muted">{{ s.description || $t('home.independentStore') }}</p>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- ===== ABOUT US (خاصتنا) ===== -->
    <section class="relative overflow-hidden py-16">
      <div class="container">
        <div class="mx-auto max-w-2xl text-center">
          <span class="chip border-primary-200 bg-primary-50 text-primary-700 dark:border-primary-600/30 dark:bg-primary-600/10">{{ $t('about.badge') }}</span>
          <h2 class="mt-4 font-heading text-3xl font-black text-ink lg:text-4xl">{{ $t('about.title') }}</h2>
          <p class="mt-4 text-lg text-muted">{{ $t('about.intro') }}</p>
        </div>

        <div class="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div v-for="v in values" :key="v.key" class="card p-6 text-center transition hover:-translate-y-0.5 hover:shadow-pop">
            <span class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-primary-50 text-primary-600 dark:bg-primary-600/10"><component :is="v.icon" class="h-7 w-7" /></span>
            <h3 class="mt-4 font-heading text-lg font-bold text-ink">{{ $t('about.values.' + v.key + '.title') }}</h3>
            <p class="mt-2 text-sm text-muted">{{ $t('about.values.' + v.key + '.text') }}</p>
          </div>
        </div>

        <!-- Stats band -->
        <div class="mt-12 grid grid-cols-2 gap-6 rounded-3xl bg-gradient-to-r from-primary-600 to-secondary-500 px-6 py-10 text-center text-white sm:grid-cols-4">
          <div v-for="s in statItems" :key="s.label">
            <p class="font-heading text-3xl font-black lg:text-4xl">{{ s.value }}</p>
            <p class="mt-1 text-sm text-white/80">{{ s.label }}</p>
          </div>
        </div>

        <div class="mt-8 text-center">
          <RouterLink :to="{ name: 'testimonials' }" class="btn btn-outline btn-lg"><Quote class="h-4 w-4" /> {{ $t('home.testimonials') }}</RouterLink>
        </div>
      </div>
    </section>

    <!-- ===== SELLER CTA ===== -->
    <section class="bg-gradient-to-br from-[#0d1526] to-primary-900">
      <div class="container flex flex-col items-center justify-between gap-6 py-12 text-center text-white lg:flex-row lg:text-start">
        <div class="flex items-center gap-4">
          <span class="hidden h-14 w-14 place-items-center rounded-2xl bg-primary-600 text-white sm:grid"><StoreIcon class="h-7 w-7" /></span>
          <div>
            <h2 class="font-heading text-2xl font-black lg:text-3xl">{{ $t('home.sellerCtaTitle') }}</h2>
            <p class="mt-2 text-slate-300">{{ $t('home.sellerCtaText') }}</p>
          </div>
        </div>
        <RouterLink :to="{ name: 'seller-login' }" class="btn btn-primary btn-lg shrink-0"><Rocket class="h-5 w-5" /> {{ $t('home.becomeSeller') }}</RouterLink>
      </div>
    </section>
  </div>
</template>
