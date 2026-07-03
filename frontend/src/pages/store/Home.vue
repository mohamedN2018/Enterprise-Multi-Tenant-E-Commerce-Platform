<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  ArrowRight,
  RotateCcw,
  Send,
  LifeBuoy,
  CreditCard,
  Lock,
  Headphones,
  Sparkles,
  ShieldCheck,
  Store as StoreIcon,
  LayoutGrid,
  Quote,
  Rocket,
  Flame,
  ChevronLeft
} from 'lucide-vue-next';
import ProductCard from '@/components/ProductCard.vue';
import ProductCarousel from '@/components/ProductCarousel.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { storefront } from '@/services/storefront';
import { useAddToCart } from '@/composables/useAddToCart';
import { heroImage, catImage, storeBanner, storeLogo, productImage, onImgError } from '@/utils/media';
import { getRecentlyViewed } from '@/utils/recent';

const router = useRouter();
const { add, adding } = useAddToCart();

const categories = ref([]);
const stores = ref([]);
const newest = ref([]);
const deals = ref([]);
const pool = ref([]);
const loading = ref(true);
const tab = ref('all');
const recent = ref(getRecentlyViewed());

// Amazon-style recommendation rails derived from the product pool.
const bestSellers = computed(() =>
  [...pool.value]
    .sort((a, b) => Number(b.rating ?? b.average_rating ?? 0) - Number(a.rating ?? a.average_rating ?? 0) || Number(b.review_count ?? 0) - Number(a.review_count ?? 0))
    .slice(0, 12)
);
const moreToConsider = computed(() => pool.value.slice(0, 12));
const alsoBought = computed(() => pool.value.slice(6, 18));
const heroBest = computed(() => bestSellers.value.slice(0, 4));

const services = [
  { icon: RotateCcw, key: 'freeReturn' },
  { icon: Send, key: 'freeShipping' },
  { icon: LifeBuoy, key: 'support' },
  { icon: CreditCard, key: 'gift' },
  { icon: Lock, key: 'secure' },
  { icon: Headphones, key: 'online' }
];

const featured = computed(() => deals.value[0] || newest.value[0] || null);
const shown = computed(() => (tab.value === 'deals' ? deals.value : newest.value).slice(0, 8));

const goCategory = (name) => router.push({ name: 'products', query: { category: name } });

onMounted(async () => {
  try {
    const [cat, st, nw, dl, pl] = await Promise.all([
      storefront.categories(),
      storefront.stores({ page_size: 6 }),
      storefront.products({ page_size: 8 }),
      storefront.products({ on_sale: 1, page_size: 8 }),
      storefront.products({ page_size: 24 })
    ]);
    categories.value = (cat.data || []).slice(0, 8);
    stores.value = st.data?.results || st.data || [];
    newest.value = nw.data?.results || nw.data || [];
    deals.value = dl.data?.results || dl.data || [];
    pool.value = pl.data?.results || pl.data || [];
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="relative overflow-hidden bg-gradient-to-br from-ink via-ink to-primary-900 text-white">
      <div class="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-primary-600/30 blur-3xl"></div>
      <div class="absolute -bottom-32 left-1/3 h-80 w-80 rounded-full bg-secondary-500/20 blur-3xl"></div>
      <div class="container relative grid gap-6 pb-10 pt-10 lg:grid-cols-[250px_1fr] lg:pb-14 lg:pt-14">
        <!-- Categories sidebar (beside the hero) -->
        <aside v-if="categories.length" class="hidden lg:block">
          <div class="overflow-hidden rounded-2xl border border-white/15 bg-white/10 backdrop-blur">
            <div class="flex items-center gap-2 border-b border-white/10 px-4 py-3 font-heading text-sm font-bold text-white">
              <LayoutGrid class="h-4 w-4 text-primary-400" /> {{ $t('nav.allCategories') }}
            </div>
            <ul class="hero-scroll max-h-[380px] overflow-y-auto py-1">
              <li v-for="c in categories" :key="c.name">
                <button class="flex w-full items-center gap-3 px-4 py-2.5 text-start text-sm text-white/90 transition hover:bg-white/10 hover:text-white" @click="goCategory(c.name)">
                  <span class="h-8 w-8 shrink-0 overflow-hidden rounded-full ring-1 ring-white/20">
                    <img :src="catImage(c.name, 64)" :alt="c.name" class="h-full w-full object-cover" @error="onImgError" />
                  </span>
                  <span class="min-w-0 flex-1 truncate">{{ c.name }}</span>
                  <span class="text-xs text-white/50">{{ c.product_count }}</span>
                  <ChevronLeft class="h-4 w-4 shrink-0 text-white/40 rtl:rotate-180" />
                </button>
              </li>
            </ul>
          </div>
        </aside>

        <!-- Hero main: text + best sellers -->
        <div class="grid items-center gap-8 lg:grid-cols-2">
          <div>
            <span class="chip border-white/20 bg-white/10 text-white"><Sparkles class="h-3.5 w-3.5 text-primary-400" /> {{ $t('home.heroBadge') }}</span>
            <h1 class="mt-5 font-heading text-4xl font-black leading-[1.1] lg:text-5xl">
              {{ $t('home.heroTitle') }} <span class="text-primary-500">{{ $t('home.heroHighlight') }}</span>
            </h1>
            <p class="mt-4 max-w-lg text-lg text-slate-300">{{ $t('home.heroSubtitle') }}</p>
            <div class="mt-8 flex flex-wrap gap-3">
              <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-lg">{{ $t('home.shopNow') }} <ArrowRight class="h-4 w-4 rtl:rotate-180" /></RouterLink>
              <RouterLink :to="{ name: 'seller-login' }" class="btn btn-light btn-lg"><Rocket class="h-4 w-4" /> {{ $t('home.becomeSeller') }}</RouterLink>
            </div>
            <div class="mt-10 flex gap-8">
              <div><p class="font-heading text-2xl font-black">{{ stores.length || '10' }}+</p><p class="text-sm text-slate-400">{{ $t('home.stores') }}</p></div>
              <div><p class="font-heading text-2xl font-black">{{ categories.length || '10' }}+</p><p class="text-sm text-slate-400">{{ $t('home.categories') }}</p></div>
              <div><p class="flex items-center gap-1 font-heading text-2xl font-black"><ShieldCheck class="h-5 w-5 text-primary-400" /> 24/7</p><p class="text-sm text-slate-400">{{ $t('home.support') }}</p></div>
            </div>
          </div>

          <!-- Best sellers showcase -->
          <div class="relative">
            <div class="absolute -inset-4 rounded-3xl bg-white/5 blur-xl"></div>
            <div class="relative rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur">
              <div class="mb-3 flex items-center justify-between">
                <p class="flex items-center gap-2 font-heading text-base font-bold text-white"><Flame class="h-5 w-5 text-secondary-400" /> {{ $t('home.bestSellers') }}</p>
                <RouterLink :to="{ name: 'products' }" class="text-xs font-medium text-primary-300 hover:text-primary-200">{{ $t('home.viewAll') }}</RouterLink>
              </div>
              <div v-if="loading" class="space-y-2">
                <div v-for="n in 4" :key="n" class="skeleton h-16 rounded-xl"></div>
              </div>
              <div v-else class="space-y-2">
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
                <p v-if="!heroBest.length" class="py-6 text-center text-sm text-white/60">{{ $t('home.ourProducts') }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Categories strip (mobile fallback) -->
        <div v-if="categories.length" class="lg:hidden">
          <div class="mb-3 flex items-center justify-between">
            <p class="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-white/70">
              <LayoutGrid class="h-4 w-4 text-primary-400" /> {{ $t('home.shopByCategory') }}
            </p>
            <RouterLink :to="{ name: 'products' }" class="text-sm font-medium text-primary-400 hover:text-primary-300">{{ $t('home.viewAll') }}</RouterLink>
          </div>
          <div class="hero-scroll flex gap-3 overflow-x-auto pb-1">
            <button
              v-for="c in categories"
              :key="c.name"
              class="flex shrink-0 items-center gap-3 rounded-full border border-white/15 bg-white/10 py-2 pe-4 ps-2 backdrop-blur transition hover:border-primary-400 hover:bg-white/20"
              @click="goCategory(c.name)"
            >
              <span class="h-9 w-9 shrink-0 overflow-hidden rounded-full ring-2 ring-white/20">
                <img :src="catImage(c.name, 80)" :alt="c.name" class="h-full w-full object-cover" @error="onImgError" />
              </span>
              <span class="whitespace-nowrap text-sm font-medium text-white">{{ c.name }}</span>
              <span class="rounded-full bg-white/15 px-2 py-0.5 text-[11px] text-white/80">{{ c.product_count }}</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Services strip -->
    <section class="border-y border-slate-100">
      <div class="container grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
        <div v-for="(s, i) in services" :key="s.key" class="flex items-center gap-3 p-5" :class="i % 2 === 0 ? 'border-e border-slate-100' : 'lg:border-e border-slate-100'">
          <component :is="s.icon" class="h-7 w-7 shrink-0 text-primary-600" />
          <div>
            <h6 class="font-heading text-sm font-bold text-ink">{{ $t('home.svc.' + s.key) }}</h6>
            <p class="text-xs text-muted">{{ $t('home.svc.' + s.key + 'Msg') }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Promo banners -->
    <section class="container grid gap-4 py-10 lg:grid-cols-2">
      <RouterLink :to="{ name: 'products', query: { on_sale: 1 } }" class="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-6 transition hover:shadow-pop">
        <div>
          <p class="mb-2 text-muted">اكتشف أفضل العروض لك!</p>
          <h3 class="font-heading text-xl font-bold text-primary-600">عروض اليوم</h3>
          <p class="font-heading text-4xl font-black text-secondary-500">40% <span class="font-normal text-primary-600">خصم</span></p>
        </div>
        <img :src="heroImage('deal1', 220, 180)" alt="" class="h-28 w-28 rounded-lg object-cover" @error="onImgError" />
      </RouterLink>
      <RouterLink :to="{ name: 'stores' }" class="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-6 transition hover:shadow-pop">
        <div>
          <p class="mb-2 text-muted">اكتشف بائعين مستقلين!</p>
          <h3 class="font-heading text-xl font-bold text-primary-600">أفضل المتاجر</h3>
          <p class="font-heading text-4xl font-black text-secondary-500">10+ <span class="font-normal text-primary-600">متجر</span></p>
        </div>
        <img :src="heroImage('deal2', 220, 180)" alt="" class="h-28 w-28 rounded-lg object-cover" @error="onImgError" />
      </RouterLink>
    </section>

    <!-- Recently viewed -->
    <section v-if="recent.length" class="container py-8">
      <h2 class="section-title mb-6">{{ $t('home.recentlyViewed') }}</h2>
      <div class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
        <ProductCard v-for="p in recent" :key="p.id" :product="p" :adding="adding === p.id" @add="add" />
      </div>
    </section>

    <!-- Recommendation rail: more to consider -->
    <div v-if="moreToConsider.length" class="container py-6">
      <ProductCarousel :title="$t('rec.moreToConsider')" :products="moreToConsider" :adding-id="adding" @add="add" />
    </div>

    <!-- Our Products -->
    <section class="container py-8">
      <div class="mb-8 flex flex-col items-center justify-between gap-4 sm:flex-row">
        <h1 class="section-title">{{ $t('home.ourProducts') }}</h1>
        <div class="flex flex-wrap gap-2">
          <button class="rounded-full px-5 py-2 text-sm font-medium transition" :class="tab === 'all' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'all'">{{ $t('home.newArrivals') }}</button>
          <button class="rounded-full px-5 py-2 text-sm font-medium transition" :class="tab === 'deals' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'deals'">{{ $t('home.onSale') }}</button>
        </div>
      </div>

      <div v-if="loading" class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
        <div v-for="n in 8" :key="n" class="rounded-xl border border-slate-200">
          <div class="skeleton aspect-[4/3] rounded-t-xl"></div>
          <div class="space-y-2 p-4"><div class="skeleton mx-auto h-4 w-2/3 rounded"></div><div class="skeleton mx-auto h-4 w-1/3 rounded"></div></div>
        </div>
      </div>
      <div v-else-if="shown.length" class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
        <ProductCard v-for="p in shown" :key="p.id" :product="p" :adding="adding === p.id" @add="add" />
      </div>
      <EmptyState v-else :title="$t('shop.noProducts')" :message="$t('home.heroSubtitle')" />

      <div class="mt-10 text-center">
        <RouterLink :to="{ name: 'products' }" class="btn btn-outline btn-lg">{{ $t('home.viewAllProducts') }} <ArrowRight class="h-4 w-4 rtl:rotate-180" /></RouterLink>
      </div>
    </section>

    <!-- Recommendation rails: best sellers + also bought -->
    <div v-if="bestSellers.length" class="container space-y-10 py-8">
      <ProductCarousel :title="$t('rec.bestSellers')" :products="bestSellers" :adding-id="adding" @add="add" />
      <ProductCarousel v-if="alsoBought.length" :title="$t('rec.alsoBought')" :products="alsoBought" :adding-id="adding" @add="add" />
    </div>

    <!-- Featured stores (moved to the end) -->
    <section v-if="stores.length" class="bg-lightbg py-14">
      <div class="container">
        <div class="mb-6 flex items-end justify-between">
          <h2 class="section-title">{{ $t('home.featuredStores') }}</h2>
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
        <div class="mt-8 text-center">
          <RouterLink :to="{ name: 'testimonials' }" class="btn btn-outline btn-lg">
            <Quote class="h-4 w-4" /> {{ $t('home.testimonials') }}
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- Seller CTA -->
    <section class="bg-ink">
      <div class="container flex flex-col items-center justify-between gap-6 py-12 text-center lg:flex-row lg:text-start">
        <div class="flex items-center gap-4">
          <span class="hidden h-14 w-14 place-items-center rounded-2xl bg-primary-600 text-white sm:grid"><StoreIcon class="h-7 w-7" /></span>
          <div>
            <h2 class="font-heading text-2xl font-black text-white lg:text-3xl">{{ $t('home.sellerCtaTitle') }}</h2>
            <p class="mt-2 text-slate-300">{{ $t('home.sellerCtaText') }}</p>
          </div>
        </div>
        <RouterLink :to="{ name: 'seller-login' }" class="btn btn-primary btn-lg shrink-0"><Rocket class="h-5 w-5" /> {{ $t('home.becomeSeller') }}</RouterLink>
      </div>
    </section>
  </div>
</template>
