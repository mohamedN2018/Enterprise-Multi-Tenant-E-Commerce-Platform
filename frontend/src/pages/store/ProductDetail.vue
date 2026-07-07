<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { Minus, Plus, ShoppingCart, Store as StoreIcon, Check, Truck, ShieldCheck, Shuffle, Heart } from 'lucide-vue-next';
import StarRating from '@/components/ui/StarRating.vue';
import PageHero from '@/components/ui/PageHero.vue';
import ProductCard from '@/components/ProductCard.vue';
import ProductCarousel from '@/components/ProductCarousel.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { storefront } from '@/services/storefront';
import { shop } from '@/services/shop';
import { useAddToCart } from '@/composables/useAddToCart';
import { useWishlist } from '@/composables/useWishlist';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { productImage, onImgError } from '@/utils/media';
import { errorMessage } from '@/services/http';
import { pushRecentlyViewed } from '@/utils/recent';
import { t } from '@/i18n';

const route = useRoute();
const auth = useAuthStore();
const ui = useUiStore();
const { add, adding } = useAddToCart();
const { add: saveWishlist, saving: wishSaving } = useWishlist();

const reviewForm = ref({ rating: 5, title: '', body: '' });
const submittingReview = ref(false);

const submitReview = async () => {
  if (!auth.isAuthenticated) {
    ui.info(t('product.signInReviewToast'));
    return;
  }
  submittingReview.value = true;
  try {
    await shop.createReview(
      { 'X-Store-Id': product.value.store },
      {
        product_id: product.value.id,
        rating: reviewForm.value.rating,
        title: reviewForm.value.title,
        body: reviewForm.value.body
      }
    );
    ui.success(t('product.reviewSubmitted'));
    reviewForm.value = { rating: 5, title: '', body: '' };
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    submittingReview.value = false;
  }
};

const product = ref(null);
const reviews = ref([]);
const summary = ref(null);
const related = ref([]);
const recommended = ref([]);
const loading = ref(true);

// Cross-store recommendation rails (Amazon-style).
const alsoBought = computed(() =>
  [...recommended.value]
    .sort((a, b) => Number(b.rating ?? b.average_rating ?? 0) - Number(a.rating ?? a.average_rating ?? 0))
    .slice(0, 12)
);
const shoppedFor = computed(() => recommended.value.slice(0, 12));
const notFound = ref(false);
const selectedVariant = ref(null);
const qty = ref(1);
const activeTab = ref('description');
const activeImage = ref(0);

const gallery = computed(() => {
  if (!product.value) return [];
  const name = product.value.name;
  // Real seller-uploaded gallery is authoritative — show exactly those photos
  // (with their alt text), never fake "other angles" from a stock service.
  const real = product.value.images || [];
  if (real.length) return real.map((x) => ({ src: x.image, alt: x.alt || name }));
  // No uploaded images yet → a single neutral placeholder (no fake stock photos).
  return [{ src: productImage(product.value, 800, 600), alt: name }];
});

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
  activeTab.value = 'description';
  try {
    const res = await storefront.product(id);
    product.value = res.data;
    pushRecentlyViewed(product.value);
    const variants = product.value.variants || [];
    selectedVariant.value = variants.find((v) => v.is_default) || variants[0] || null;
    const [rev, rel, rec] = await Promise.all([
      storefront.productReviews(id),
      storefront.products({ store: product.value.store_slug, page_size: 5 }),
      storefront.products({ page_size: 20 })
    ]);
    reviews.value = rev.data?.results || [];
    summary.value = rev.data?.summary || null;
    related.value = (rel.data?.results || rel.data || []).filter((x) => x.id !== id).slice(0, 4);
    recommended.value = (rec.data?.results || rec.data || []).filter((x) => x.id !== id);
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
  <div>
    <PageHero :title="$t('product.shopDetail')" :items="[{ label: $t('shop.title'), to: { name: 'products' } }, { label: $t('product.detail') }]" />

    <div class="container py-10">
      <div v-if="loading" class="flex min-h-[40vh] items-center justify-center"><Spinner :size="28" :label="$t('product.loading')" /></div>

      <EmptyState v-else-if="notFound" :title="$t('product.notFound')" :message="$t('product.notFoundMsg')">
        <RouterLink :to="{ name: 'products' }" class="btn btn-primary btn-sm">{{ $t('product.browseProducts') }}</RouterLink>
      </EmptyState>

      <template v-else-if="product">
        <div class="grid gap-10 lg:grid-cols-2">
          <!-- Gallery -->
          <div>
            <div class="overflow-hidden rounded-xl border border-slate-200 bg-lightbg">
              <img :src="gallery[activeImage]?.src" :alt="gallery[activeImage]?.alt || product.name" class="aspect-square w-full object-cover" @error="onImgError" />
            </div>
            <div v-if="gallery.length > 1" class="mt-4 flex justify-center gap-3">
              <button
                v-for="(g, i) in gallery"
                :key="i"
                class="overflow-hidden rounded-full border-2 transition"
                :class="i === activeImage ? 'h-20 w-20 border-secondary-500' : 'h-16 w-16 border-primary-600'"
                @click="activeImage = i"
              >
                <img :src="g.src" :alt="g.alt" class="h-full w-full object-cover" @error="onImgError" />
              </button>
            </div>
          </div>

          <!-- Info -->
          <div>
            <RouterLink v-if="product.store_slug" :to="{ name: 'store', params: { slug: product.store_slug } }" class="inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:underline">
              <StoreIcon class="h-4 w-4" /> {{ product.store_slug }}
            </RouterLink>
            <h1 class="mt-2 font-heading text-3xl font-bold text-ink">{{ product.name }}</h1>
            <div class="mt-3"><StarRating :value="Number(product.rating || 0)" :count="product.review_count || 0" /></div>

            <div class="mt-5 flex items-end gap-3">
              <span class="font-heading text-4xl font-bold text-primary-600">{{ price }} {{ currency }}</span>
              <del v-if="onSale" class="mb-1 text-lg text-slate-400">{{ compareAt }} {{ currency }}</del>
              <span v-if="onSale" class="mb-1 rounded-full bg-secondary-500 px-3 py-0.5 text-xs font-bold text-white">{{ $t('product.sale') }}</span>
            </div>

            <p v-if="product.description" class="mt-5 whitespace-pre-line leading-7 text-muted">{{ product.description }}</p>

            <div v-if="product.variants?.length > 1" class="mt-6">
              <p class="label">{{ $t('product.options') }}</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="v in product.variants"
                  :key="v.id"
                  class="chip"
                  :class="selectedVariant?.id === v.id ? 'border-primary-600 bg-primary-50 text-primary-700' : 'border-slate-200 text-muted hover:border-slate-300'"
                  :disabled="v.in_stock === false"
                  @click="selectedVariant = v"
                >
                  {{ v.name }} <span v-if="v.in_stock === false" class="text-slate-400">({{ $t('product.out') }})</span>
                </button>
              </div>
            </div>

            <div class="mt-6 flex flex-wrap items-center gap-4">
              <div class="inline-flex items-center rounded-full border border-slate-200">
                <button class="grid h-11 w-11 place-items-center rounded-full text-ink hover:bg-lightbg disabled:opacity-40" :disabled="qty <= 1" @click="qty--"><Minus class="h-4 w-4" /></button>
                <span class="w-10 text-center font-semibold">{{ qty }}</span>
                <button class="grid h-11 w-11 place-items-center rounded-full text-ink hover:bg-lightbg" @click="qty++"><Plus class="h-4 w-4" /></button>
              </div>
              <button class="btn btn-primary btn-lg flex-1 border border-secondary-500 sm:flex-none" :disabled="!inStock || adding === product.id" @click="addToCart">
                <ShoppingCart class="h-5 w-5" /> {{ inStock ? $t('product.addToCart') : $t('product.outOfStock') }}
              </button>
              <button class="grid h-12 w-12 place-items-center rounded-full border border-slate-200 text-primary-600 hover:border-primary-500 disabled:opacity-50" :title="$t('product.wishlist')" :disabled="wishSaving === product.id" @click="saveWishlist(product, { variant: selectedVariant })"><Heart class="h-5 w-5" /></button>
              <RouterLink :to="{ name: 'products', query: { store: product.store_slug } }" class="grid h-12 w-12 place-items-center rounded-full border border-slate-200 text-primary-600 hover:border-primary-500" :title="$t('product.moreFromStore')"><Shuffle class="h-5 w-5" /></RouterLink>
            </div>

            <div class="mt-6 flex items-center gap-1.5 text-sm" :class="inStock ? 'text-emerald-600' : 'text-secondary-500'">
              <Check v-if="inStock" class="h-4 w-4" /> {{ inStock ? $t('product.inStock') : $t('product.unavailable') }}
            </div>
            <div class="mt-6 grid gap-3 border-t border-slate-100 pt-6 sm:grid-cols-2">
              <div class="flex items-center gap-2 text-sm text-muted"><Truck class="h-4 w-4 text-primary-600" /> {{ $t('product.fastDelivery') }}</div>
              <div class="flex items-center gap-2 text-sm text-muted"><ShieldCheck class="h-4 w-4 text-primary-600" /> {{ $t('product.securePayment') }}</div>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="mt-14">
          <div class="flex gap-6 border-b border-slate-200">
            <button class="border-b-2 pb-3 font-heading font-semibold transition" :class="activeTab === 'description' ? 'border-secondary-500 text-ink' : 'border-transparent text-muted hover:text-ink'" @click="activeTab = 'description'">{{ $t('product.description') }}</button>
            <button class="border-b-2 pb-3 font-heading font-semibold transition" :class="activeTab === 'reviews' ? 'border-secondary-500 text-ink' : 'border-transparent text-muted hover:text-ink'" @click="activeTab = 'reviews'">{{ $t('product.reviews') }} ({{ summary?.count || 0 }})</button>
          </div>

          <div v-if="activeTab === 'description'" class="prose mt-6 max-w-none leading-7 text-muted">
            <p class="whitespace-pre-line">{{ product.description || $t('product.noDescription') }}</p>
          </div>

          <div v-else class="mt-6 grid gap-8 lg:grid-cols-[280px_1fr]">
            <div class="h-fit rounded-xl border border-slate-200 p-6 text-center">
              <p class="font-heading text-4xl font-bold text-ink">{{ (summary?.average_rating || 0).toFixed(1) }}</p>
              <div class="mt-2 flex justify-center"><StarRating :value="summary?.average_rating || 0" /></div>
              <p class="mt-1 text-sm text-muted">{{ summary?.count || 0 }} {{ $t('product.reviewsCount') }}</p>
              <div v-if="summary?.distribution" class="mt-5 space-y-1.5">
                <div v-for="n in [5, 4, 3, 2, 1]" :key="n" class="flex items-center gap-2 text-xs">
                  <span class="w-6 text-muted">{{ n }}★</span>
                  <div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <div class="h-full rounded-full bg-primary-600" :style="{ width: `${summary.count ? ((summary.distribution[n] || 0) / summary.count) * 100 : 0}%` }"></div>
                  </div>
                  <span class="w-6 text-right text-muted">{{ summary.distribution[n] || 0 }}</span>
                </div>
              </div>
            </div>
            <div>
              <!-- Write a review -->
              <div class="mb-6 rounded-xl border border-slate-200 p-5">
                <h4 class="mb-3 font-heading font-semibold text-ink">{{ $t('product.writeReview') }}</h4>
                <template v-if="auth.isAuthenticated">
                  <form class="space-y-3" @submit.prevent="submitReview">
                    <div class="flex items-center gap-3">
                      <span class="text-sm text-muted">{{ $t('product.yourRating') }}</span>
                      <StarRating :value="reviewForm.rating" editable :size="22" @update:value="reviewForm.rating = $event" />
                    </div>
                    <input v-model="reviewForm.title" class="input" :placeholder="$t('product.reviewTitle')" maxlength="150" />
                    <textarea v-model="reviewForm.body" rows="3" class="input" :placeholder="$t('product.reviewBody')"></textarea>
                    <button type="submit" class="btn btn-primary btn-sm" :disabled="submittingReview">
                      <Spinner v-if="submittingReview" :size="16" /><span v-else>{{ $t('product.submitReview') }}</span>
                    </button>
                  </form>
                </template>
                <p v-else class="text-sm text-muted">
                  <RouterLink :to="{ name: 'login', query: { redirect: route.fullPath } }" class="font-semibold text-primary-600 hover:underline">{{ $t('product.signInToReview') }}</RouterLink>
                  {{ $t('product.toWriteReview') }}
                </p>
              </div>

              <div v-if="reviews.length" class="space-y-4">
                <article v-for="r in reviews" :key="r.id" class="rounded-xl border border-slate-200 p-5">
                  <div class="flex items-center justify-between">
                    <StarRating :value="r.rating" :size="14" />
                    <span v-if="r.is_verified_purchase" class="chip border-emerald-200 bg-emerald-50 text-emerald-700"><Check class="h-3 w-3" /> {{ $t('product.verified') }}</span>
                  </div>
                  <h4 v-if="r.title" class="mt-2 font-semibold text-ink">{{ r.title }}</h4>
                  <p class="mt-1 text-sm text-muted">{{ r.body }}</p>
                </article>
              </div>
              <EmptyState v-else :title="$t('product.noReviews')" :message="$t('product.noReviewsMsg')" />
            </div>
          </div>
        </div>

        <!-- Related -->
        <div v-if="related.length" class="mt-14">
          <h2 class="section-title mb-6">{{ $t('product.related') }}</h2>
          <div class="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
            <ProductCard v-for="rp in related" :key="rp.id" :product="rp" :adding="adding === rp.id" @add="add" />
          </div>
        </div>

        <!-- Recommendation rails -->
        <div v-if="alsoBought.length" class="mt-14 space-y-12">
          <ProductCarousel :title="$t('rec.alsoBought')" :products="alsoBought" :adding-id="adding" @add="add" />
          <ProductCarousel v-if="shoppedFor.length" :title="$t('rec.shoppedFor')" :products="shoppedFor" :adding-id="adding" @add="add" />
        </div>
      </template>
    </div>
  </div>
</template>
