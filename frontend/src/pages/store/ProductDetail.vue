<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { Minus, Plus, ShoppingCart, Store as StoreIcon, Check, Truck, ShieldCheck } from 'lucide-vue-next';
import StarRating from '@/components/ui/StarRating.vue';
import Breadcrumbs from '@/components/ui/Breadcrumbs.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { storefront } from '@/services/storefront';
import { useAddToCart } from '@/composables/useAddToCart';
import { productImage, onImgError } from '@/utils/media';

const route = useRoute();
const { add, adding } = useAddToCart();

const product = ref(null);
const reviews = ref([]);
const summary = ref(null);
const loading = ref(true);
const notFound = ref(false);
const selectedVariant = ref(null);
const qty = ref(1);

const gallery = computed(() =>
  product.value ? [productImage(product.value, 800, 600), productImage({ id: `${product.value.id}-2` }, 800, 600), productImage({ id: `${product.value.id}-3` }, 800, 600)] : []
);
const activeImage = ref(0);

const currency = computed(() => product.value?.currency || '');
const price = computed(() => selectedVariant.value?.price ?? product.value?.price);
const compareAt = computed(() => selectedVariant.value?.compare_at_price);
const onSale = computed(() => compareAt.value && Number(compareAt.value) > Number(price.value));
const inStock = computed(() => selectedVariant.value?.in_stock !== false);

const load = async (id) => {
  loading.value = true;
  notFound.value = false;
  activeImage.value = 0;
  qty.value = 1;
  try {
    const res = await storefront.product(id);
    product.value = res.data;
    const variants = product.value.variants || [];
    selectedVariant.value = variants.find((v) => v.is_default) || variants[0] || null;
    const rev = await storefront.productReviews(id);
    reviews.value = rev.data?.results || [];
    summary.value = rev.data?.summary || null;
  } catch {
    notFound.value = true;
  } finally {
    loading.value = false;
  }
};

const addToCart = () => add(product.value, { variant: selectedVariant.value, quantity: qty.value });

watch(() => route.params.id, (id) => id && load(id), { immediate: true });
</script>

<template>
  <div class="container py-8">
    <div v-if="loading" class="flex min-h-[40vh] items-center justify-center">
      <Spinner :size="28" label="Loading product…" />
    </div>

    <EmptyState
      v-else-if="notFound"
      title="Product not found"
      message="This product may have been removed or is no longer available."
    >
      <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-sm">Browse products</RouterLink>
    </EmptyState>

    <template v-else-if="product">
      <Breadcrumbs
        :items="[
          { label: 'Home', to: { name: 'home' } },
          { label: 'Products', to: { name: 'products' } },
          { label: product.name }
        ]"
      />

      <div class="mt-4 grid gap-8 lg:grid-cols-2">
        <!-- Gallery -->
        <div>
          <div class="aspect-square overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
            <img :src="gallery[activeImage]" :alt="product.name" class="h-full w-full object-cover" @error="onImgError" />
          </div>
          <div class="mt-3 flex gap-3">
            <button
              v-for="(g, i) in gallery"
              :key="i"
              class="h-20 w-20 overflow-hidden rounded-lg border-2 transition"
              :class="i === activeImage ? 'border-primary-500' : 'border-transparent'"
              @click="activeImage = i"
            >
              <img :src="g" alt="" class="h-full w-full object-cover" @error="onImgError" />
            </button>
          </div>
        </div>

        <!-- Info -->
        <div>
          <RouterLink
            v-if="product.store_slug"
            :to="{ name: 'products', query: { store: product.store_slug } }"
            class="inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:underline"
          >
            <StoreIcon class="h-4 w-4" /> {{ product.store_slug }}
          </RouterLink>
          <h1 class="mt-2 text-3xl font-bold">{{ product.name }}</h1>

          <div class="mt-3 flex items-center gap-3">
            <StarRating :value="Number(product.rating || 0)" :count="product.review_count || 0" />
          </div>

          <div class="mt-5 flex items-end gap-3">
            <span class="text-3xl font-bold">{{ price }} {{ currency }}</span>
            <span v-if="onSale" class="mb-1 text-lg text-slate-400 line-through">{{ compareAt }} {{ currency }}</span>
            <span v-if="onSale" class="mb-1 rounded-md bg-rose-100 px-2 py-0.5 text-xs font-bold text-rose-700">Sale</span>
          </div>

          <p v-if="product.description" class="mt-5 whitespace-pre-line text-slate-600">{{ product.description }}</p>

          <!-- Variants -->
          <div v-if="product.variants?.length > 1" class="mt-6">
            <p class="label">Options</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="v in product.variants"
                :key="v.id"
                class="chip"
                :class="selectedVariant?.id === v.id
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-slate-200 text-slate-600 hover:border-slate-300'"
                :disabled="v.in_stock === false"
                @click="selectedVariant = v"
              >
                {{ v.name }}
                <span v-if="v.in_stock === false" class="text-slate-400">(out)</span>
              </button>
            </div>
          </div>

          <!-- Qty + add -->
          <div class="mt-6 flex flex-wrap items-center gap-4">
            <div class="inline-flex items-center rounded-lg border border-slate-200">
              <button class="grid h-10 w-10 place-items-center text-slate-600 hover:bg-slate-100 disabled:opacity-40" :disabled="qty <= 1" @click="qty--">
                <Minus class="h-4 w-4" />
              </button>
              <span class="w-10 text-center text-sm font-semibold">{{ qty }}</span>
              <button class="grid h-10 w-10 place-items-center text-slate-600 hover:bg-slate-100" @click="qty++">
                <Plus class="h-4 w-4" />
              </button>
            </div>
            <button class="btn btn-primary btn-lg flex-1 sm:flex-none" :disabled="!inStock || adding === product.id" @click="addToCart">
              <ShoppingCart class="h-5 w-5" />
              {{ inStock ? 'Add to cart' : 'Out of stock' }}
            </button>
          </div>

          <div class="mt-6 flex items-center gap-1.5 text-sm" :class="inStock ? 'text-emerald-600' : 'text-rose-600'">
            <Check v-if="inStock" class="h-4 w-4" />
            {{ inStock ? 'In stock and ready to ship' : 'Currently unavailable' }}
          </div>

          <div class="mt-6 grid gap-3 border-t border-slate-100 pt-6 sm:grid-cols-2">
            <div class="flex items-center gap-2 text-sm text-slate-600"><Truck class="h-4 w-4 text-primary-600" /> Fast, tracked delivery</div>
            <div class="flex items-center gap-2 text-sm text-slate-600"><ShieldCheck class="h-4 w-4 text-primary-600" /> Secure payment</div>
          </div>
        </div>
      </div>

      <!-- Reviews -->
      <section class="mt-14">
        <h2 class="section-title mb-5">Customer reviews</h2>
        <div class="grid gap-8 lg:grid-cols-[280px_1fr]">
          <div class="card h-fit p-6 text-center">
            <p class="text-4xl font-bold">{{ (summary?.average_rating || 0).toFixed(1) }}</p>
            <div class="mt-2 flex justify-center">
              <StarRating :value="summary?.average_rating || 0" />
            </div>
            <p class="mt-1 text-sm text-slate-500">{{ summary?.count || 0 }} reviews</p>
            <div v-if="summary?.distribution" class="mt-5 space-y-1.5">
              <div v-for="n in [5, 4, 3, 2, 1]" :key="n" class="flex items-center gap-2 text-xs">
                <span class="w-6 text-slate-500">{{ n }}★</span>
                <div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                  <div
                    class="h-full rounded-full bg-amber-400"
                    :style="{ width: `${summary.count ? ((summary.distribution[n] || 0) / summary.count) * 100 : 0}%` }"
                  ></div>
                </div>
                <span class="w-6 text-right text-slate-400">{{ summary.distribution[n] || 0 }}</span>
              </div>
            </div>
          </div>

          <div>
            <div v-if="reviews.length" class="space-y-4">
              <article v-for="r in reviews" :key="r.id" class="card p-5">
                <div class="flex items-center justify-between">
                  <StarRating :value="r.rating" :size="14" />
                  <span v-if="r.is_verified_purchase" class="chip border-emerald-200 bg-emerald-50 text-emerald-700">
                    <Check class="h-3 w-3" /> Verified purchase
                  </span>
                </div>
                <h4 v-if="r.title" class="mt-2 font-semibold">{{ r.title }}</h4>
                <p class="mt-1 text-sm text-slate-600">{{ r.body }}</p>
              </article>
            </div>
            <EmptyState v-else title="No reviews yet" message="Be the first to review this product after purchase." />
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
