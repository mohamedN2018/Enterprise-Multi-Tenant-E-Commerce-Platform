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
  ShoppingCart
} from 'lucide-vue-next';
import ProductCard from '@/components/ProductCard.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { storefront } from '@/services/storefront';
import { useAddToCart } from '@/composables/useAddToCart';
import { heroImage, catImage, onImgError } from '@/utils/media';

const router = useRouter();
const { add, adding } = useAddToCart();

const categories = ref([]);
const newest = ref([]);
const deals = ref([]);
const loading = ref(true);
const tab = ref('all');

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
    const [cat, nw, dl] = await Promise.all([
      storefront.categories(),
      storefront.products({ page_size: 8 }),
      storefront.products({ on_sale: 1, page_size: 8 })
    ]);
    categories.value = (cat.data || []).slice(0, 8);
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
    <section class="bg-lightbg">
      <div class="container grid gap-4 py-8 lg:grid-cols-3">
        <!-- Main promo -->
        <div class="relative overflow-hidden rounded-xl bg-white lg:col-span-2">
          <div class="grid h-full items-center gap-4 p-8 sm:grid-cols-2">
            <div>
              <h4 class="mb-3 font-heading font-bold uppercase tracking-[3px] text-secondary-500">Save up to $400</h4>
              <h1 class="mb-4 font-heading text-3xl font-black leading-tight text-ink lg:text-4xl">
                On selected Laptops, Desktops & Smartphones
              </h1>
              <p class="mb-6 text-muted">Terms and conditions apply.</p>
              <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-lg">Shop Now <ArrowRight class="h-4 w-4" /></RouterLink>
            </div>
            <img :src="heroImage('electro', 700, 560)" alt="" class="ml-auto hidden max-h-72 w-full rounded-lg object-cover sm:block" @error="onImgError" />
          </div>
        </div>

        <!-- Side offer banner -->
        <RouterLink :to="featured ? { name: 'product', params: { id: featured.id } } : { name: 'products' }" class="group relative overflow-hidden rounded-xl">
          <img :src="heroImage('offer', 500, 560)" alt="" class="h-full min-h-64 w-full object-cover" @error="onImgError" />
          <div class="absolute left-4 top-4 flex items-center gap-2">
            <span class="rounded bg-primary-600 px-3 py-1 text-sm font-semibold text-white">Special Offer</span>
          </div>
          <div class="absolute inset-x-0 bottom-0 bg-ink/50 p-5 text-center text-white">
            <p class="text-sm text-white/80">{{ featured?.store_slug || 'Featured store' }}</p>
            <p class="clamp-1 font-heading text-xl font-bold">{{ featured?.name || 'Top pick of the week' }}</p>
            <p class="mt-1 text-primary-400">
              <del v-if="featured?.compare_at_price" class="mr-2 text-white/60">{{ featured.compare_at_price }}</del>
              <span class="font-semibold text-white">{{ featured?.price }} {{ featured?.currency }}</span>
            </p>
            <span class="btn btn-primary mt-3"><ShoppingCart class="h-4 w-4" /> Shop offer</span>
          </div>
        </RouterLink>
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
  </div>
</template>
