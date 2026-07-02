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
  Quote,
  Star,
  Rocket
} from 'lucide-vue-next';
import ProductCard from '@/components/ProductCard.vue';
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
const loading = ref(true);
const tab = ref('all');
const recent = ref(getRecentlyViewed());

const testimonials = [
  { name: 'Sarah M.', text: 'Fast shipping and the product quality exceeded my expectations. My go-to marketplace now!', role: 'Verified buyer' },
  { name: 'Ahmed K.', text: 'Love the variety of independent stores. Found exactly what I was looking for at a great price.', role: 'Verified buyer' },
  { name: 'Elena R.', text: 'Checkout was smooth and the wishlist feature is so handy. Highly recommend q-shop.', role: 'Verified buyer' }
];

const services = [
  { icon: RotateCcw, title: 'Free Return', text: '30 days money back guarantee!' },
  { icon: Send, title: 'Free Shipping', text: 'Free shipping on all orders' },
  { icon: LifeBuoy, title: 'Support 24/7', text: 'We support online 24 hrs a day' },
  { icon: CreditCard, title: 'Gift Cards', text: 'Receive a gift on orders over $50' },
  { icon: Lock, title: 'Secure Payment', text: 'We value your security' },
  { icon: Headphones, title: 'Online Service', text: 'Free returns within 30 days' }
];

const featured = computed(() => deals.value[0] || newest.value[0] || null);
const shown = computed(() => (tab.value === 'deals' ? deals.value : newest.value).slice(0, 8));

const goCategory = (name) => router.push({ name: 'products', query: { category: name } });

onMounted(async () => {
  try {
    const [cat, st, nw, dl] = await Promise.all([
      storefront.categories(),
      storefront.stores({ page_size: 6 }),
      storefront.products({ page_size: 8 }),
      storefront.products({ on_sale: 1, page_size: 8 })
    ]);
    categories.value = (cat.data || []).slice(0, 8);
    stores.value = st.data?.results || st.data || [];
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
    <section class="relative overflow-hidden bg-gradient-to-br from-ink via-ink to-primary-900 text-white">
      <div class="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-primary-600/30 blur-3xl"></div>
      <div class="absolute -bottom-32 left-1/3 h-80 w-80 rounded-full bg-secondary-500/20 blur-3xl"></div>
      <div class="container relative grid items-center gap-10 py-16 lg:grid-cols-2 lg:py-24">
        <div>
          <span class="chip border-white/20 bg-white/10 text-white"><Sparkles class="h-3.5 w-3.5 text-primary-400" /> Welcome to q-shop</span>
          <h1 class="mt-5 font-heading text-4xl font-black leading-[1.1] lg:text-5xl">
            Everything you love, from <span class="text-primary-500">independent stores</span>
          </h1>
          <p class="mt-4 max-w-lg text-lg text-slate-300">
            Shop thousands of products across electronics, fashion, home and more — one cart, secure checkout, and fast delivery from verified sellers.
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-lg">Shop now <ArrowRight class="h-4 w-4" /></RouterLink>
            <RouterLink :to="{ name: 'register' }" class="btn btn-light btn-lg"><Rocket class="h-4 w-4" /> Become a seller</RouterLink>
          </div>
          <div class="mt-10 flex gap-8">
            <div><p class="font-heading text-2xl font-black">{{ stores.length || '10' }}+</p><p class="text-sm text-slate-400">Stores</p></div>
            <div><p class="font-heading text-2xl font-black">{{ categories.length || '10' }}+</p><p class="text-sm text-slate-400">Categories</p></div>
            <div><p class="flex items-center gap-1 font-heading text-2xl font-black"><ShieldCheck class="h-5 w-5 text-primary-400" /> 24/7</p><p class="text-sm text-slate-400">Support</p></div>
          </div>
        </div>

        <!-- Featured product card -->
        <div class="relative mx-auto w-full max-w-sm lg:max-w-md">
          <div class="absolute -inset-4 rounded-3xl bg-white/5 blur-xl"></div>
          <RouterLink :to="featured ? { name: 'product', params: { id: featured.id } } : { name: 'products' }" class="relative block overflow-hidden rounded-2xl bg-white text-ink shadow-pop transition hover:-translate-y-1">
            <div class="relative">
              <img :src="featured ? productImage(featured, 800, 500) : heroImage('hero', 800, 500)" alt="" class="h-60 w-full object-cover" @error="onImgError" />
              <span class="absolute left-4 top-4 rounded-full bg-secondary-500 px-3 py-1 text-xs font-bold text-white">Featured</span>
            </div>
            <div class="p-5">
              <p class="text-xs font-medium text-primary-600">{{ featured?.store_slug || 'q-shop' }}</p>
              <p class="clamp-1 font-heading text-lg font-bold">{{ featured?.name || 'Discover top picks' }}</p>
              <div class="mt-3 flex items-center justify-between">
                <span class="font-heading text-xl font-bold text-primary-600">{{ featured?.price }} {{ featured?.currency }}</span>
                <span class="btn btn-primary btn-sm">View <ArrowRight class="h-4 w-4" /></span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- Services strip -->
    <section class="border-y border-slate-100">
      <div class="container grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
        <div v-for="(s, i) in services" :key="s.title" class="flex items-center gap-3 p-5" :class="i % 2 === 0 ? 'border-r border-slate-100' : 'lg:border-r border-slate-100'">
          <component :is="s.icon" class="h-7 w-7 shrink-0 text-primary-600" />
          <div>
            <h6 class="font-heading text-sm font-bold uppercase text-ink">{{ s.title }}</h6>
            <p class="text-xs text-muted">{{ s.text }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Category strip -->
    <section v-if="categories.length" class="bg-lightbg py-10">
      <div class="container">
        <h2 class="section-title mb-6 text-center">Shop by Category</h2>
        <div class="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-8">
          <button v-for="c in categories" :key="c.name" class="group flex flex-col items-center gap-2" @click="goCategory(c.name)">
            <span class="h-24 w-24 overflow-hidden rounded-full border-2 border-transparent transition group-hover:border-primary-600">
              <img :src="catImage(c.name)" :alt="c.name" class="h-full w-full object-cover" @error="onImgError" />
            </span>
            <span class="text-center text-sm font-medium text-ink group-hover:text-primary-600">{{ c.name }}</span>
            <span class="text-xs text-muted">{{ c.product_count }} items</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Featured stores -->
    <section v-if="stores.length" class="container py-10">
      <div class="mb-6 flex items-end justify-between">
        <h2 class="section-title">Featured Stores</h2>
        <RouterLink :to="{ name: 'stores' }" class="text-sm font-medium text-primary-600 hover:underline">View all</RouterLink>
      </div>
      <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <RouterLink v-for="s in stores" :key="s.id" :to="{ name: 'store', params: { slug: s.slug } }" class="card group overflow-hidden transition hover:-translate-y-0.5 hover:shadow-pop">
          <div class="h-24 overflow-hidden bg-lightbg"><img :src="storeBanner(s)" alt="" class="h-full w-full object-cover transition group-hover:scale-105" @error="onImgError" /></div>
          <div class="flex items-center gap-3 p-4">
            <img :src="storeLogo(s)" :alt="s.name" class="-mt-8 h-12 w-12 rounded-xl border-2 border-white object-cover shadow" @error="onImgError" />
            <div class="min-w-0">
              <p class="truncate font-heading font-semibold group-hover:text-primary-600">{{ s.name }}</p>
              <p class="clamp-1 text-xs text-muted">{{ s.description || 'Independent store' }}</p>
            </div>
          </div>
        </RouterLink>
      </div>
    </section>

    <!-- Promo banners -->
    <section class="container grid gap-4 py-10 lg:grid-cols-2">
      <RouterLink :to="{ name: 'products', query: { on_sale: 1 } }" class="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-6 transition hover:shadow-pop">
        <div>
          <p class="mb-2 text-muted">Find the best deals for you!</p>
          <h3 class="font-heading text-xl font-bold text-primary-600">Today's Deals</h3>
          <p class="font-heading text-4xl font-black text-secondary-500">40% <span class="font-normal text-primary-600">Off</span></p>
        </div>
        <img :src="heroImage('deal1', 220, 180)" alt="" class="h-28 w-28 rounded-lg object-cover" @error="onImgError" />
      </RouterLink>
      <RouterLink :to="{ name: 'stores' }" class="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-6 transition hover:shadow-pop">
        <div>
          <p class="mb-2 text-muted">Discover independent sellers!</p>
          <h3 class="font-heading text-xl font-bold text-primary-600">Top Stores</h3>
          <p class="font-heading text-4xl font-black text-secondary-500">10+ <span class="font-normal text-primary-600">Shops</span></p>
        </div>
        <img :src="heroImage('deal2', 220, 180)" alt="" class="h-28 w-28 rounded-lg object-cover" @error="onImgError" />
      </RouterLink>
    </section>

    <!-- Recently viewed -->
    <section v-if="recent.length" class="container py-8">
      <h2 class="section-title mb-6">Recently Viewed</h2>
      <div class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
        <ProductCard v-for="p in recent" :key="p.id" :product="p" :adding="adding === p.id" @add="add" />
      </div>
    </section>

    <!-- Our Products -->
    <section class="container py-8">
      <div class="mb-8 flex flex-col items-center justify-between gap-4 sm:flex-row">
        <h1 class="section-title">Our Products</h1>
        <div class="flex flex-wrap gap-2">
          <button class="rounded-full px-5 py-2 text-sm font-medium transition" :class="tab === 'all' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'all'">New Arrivals</button>
          <button class="rounded-full px-5 py-2 text-sm font-medium transition" :class="tab === 'deals' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'deals'">On Sale</button>
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
      <EmptyState v-else title="No products yet" message="Check back soon for new arrivals." />

      <div class="mt-10 text-center">
        <RouterLink :to="{ name: 'products' }" class="btn btn-outline btn-lg">View all products <ArrowRight class="h-4 w-4" /></RouterLink>
      </div>
    </section>

    <!-- Testimonials -->
    <section class="bg-lightbg py-14">
      <div class="container">
        <h2 class="section-title mb-8 text-center">What our customers say</h2>
        <div class="grid gap-6 md:grid-cols-3">
          <div v-for="t in testimonials" :key="t.name" class="card p-6">
            <Quote class="h-8 w-8 text-primary-200" />
            <p class="mt-3 text-muted">{{ t.text }}</p>
            <div class="mt-4 flex items-center gap-3">
              <span class="grid h-10 w-10 place-items-center rounded-full bg-primary-100 font-bold text-primary-700">{{ t.name.charAt(0) }}</span>
              <div>
                <p class="font-semibold">{{ t.name }}</p>
                <p class="flex items-center gap-1 text-xs text-muted"><Star class="h-3 w-3 fill-primary-600 text-primary-600" /> {{ t.role }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Seller CTA -->
    <section class="bg-ink">
      <div class="container flex flex-col items-center justify-between gap-6 py-12 text-center lg:flex-row lg:text-left">
        <div class="flex items-center gap-4">
          <span class="hidden h-14 w-14 place-items-center rounded-2xl bg-primary-600 text-white sm:grid"><StoreIcon class="h-7 w-7" /></span>
          <div>
            <h2 class="font-heading text-2xl font-black text-white lg:text-3xl">Start selling on q-shop today</h2>
            <p class="mt-2 text-slate-300">Open your store, reach thousands of shoppers, and grow your business.</p>
          </div>
        </div>
        <RouterLink :to="{ name: 'register' }" class="btn btn-primary btn-lg shrink-0"><Rocket class="h-5 w-5" /> Become a seller</RouterLink>
      </div>
    </section>
  </div>
</template>
