<script setup>
import { computed } from 'vue';
import { Eye, ShoppingCart, Star, Shuffle, Heart } from 'lucide-vue-next';
import { productImage, onImgError } from '@/utils/media';

const props = defineProps({
  product: { type: Object, required: true },
  adding: { type: Boolean, default: false }
});
const emit = defineEmits(['add']);

const p = computed(() => props.product);
const to = computed(() => ({ name: 'product', params: { id: p.value.id } }));
const img = computed(
  () => p.value.primary_image?.image || p.value.image || p.value.images?.[0]?.image || productImage(p.value)
);
const currency = computed(() => p.value.currency || p.value.store?.currency || '');
const price = computed(() => p.value.price ?? p.value.min_price ?? p.value.display_price);
const compareAt = computed(() => p.value.compare_at_price);
const onSale = computed(() => compareAt.value && Number(compareAt.value) > Number(price.value));
const rating = computed(() => Math.round(Number(p.value.rating ?? p.value.average_rating ?? 0)));
const storeName = computed(() => p.value.store?.name || p.value.store_slug);
</script>

<template>
  <div class="product-card group relative rounded-xl">
    <div class="h-full rounded-xl border border-slate-200 transition group-hover:rounded-b-none group-hover:border-b-0">
      <!-- Media -->
      <div class="product-media relative overflow-hidden rounded-t-xl">
        <RouterLink :to="to">
          <img :src="img" :alt="p.name" loading="lazy" class="aspect-[4/3] w-full object-cover" @error="onImgError" />
        </RouterLink>
        <div v-if="onSale" class="corner-badge bg-secondary-500">Sale</div>
        <div v-else-if="p.is_new" class="corner-badge bg-primary-600">New</div>
        <RouterLink :to="to" class="product-eye absolute inset-0 flex items-center justify-center bg-white/20 opacity-0">
          <span class="grid h-12 w-12 place-items-center rounded-full bg-primary-600 text-white transition hover:bg-secondary-500">
            <Eye class="h-5 w-5" />
          </span>
        </RouterLink>
      </div>

      <!-- Body -->
      <div class="rounded-b-xl p-4 text-center">
        <RouterLink v-if="storeName" :to="{ name: 'products', query: { store: p.store_slug } }" class="mb-1 block text-sm text-muted hover:text-primary-600">
          {{ storeName }}
        </RouterLink>
        <RouterLink :to="to" class="clamp-2 block font-heading text-lg font-semibold text-ink hover:text-primary-600">
          {{ p.name }}
        </RouterLink>
        <div class="mt-2">
          <del v-if="onSale" class="mr-2 text-slate-400">{{ compareAt }}</del>
          <span class="text-lg font-semibold text-primary-600">{{ price }} {{ currency }}</span>
        </div>
      </div>
    </div>

    <!-- Slide-up actions -->
    <div class="product-actions absolute inset-x-0 top-full z-10 rounded-b-xl border border-t-0 border-slate-200 bg-white px-4 pb-4 text-center">
      <button class="btn btn-primary mb-3 w-full border border-secondary-500" :disabled="adding" @click="emit('add', p)">
        <ShoppingCart class="h-4 w-4" /> {{ adding ? 'Adding…' : 'Add To Cart' }}
      </button>
      <div class="flex items-center justify-between">
        <div class="flex">
          <Star v-for="n in 5" :key="n" class="h-4 w-4" :class="n <= rating ? 'fill-primary-600 text-primary-600' : 'text-slate-300'" />
        </div>
        <div class="flex gap-2">
          <RouterLink :to="{ name: 'products', query: { store: p.store_slug } }" class="grid h-8 w-8 place-items-center rounded-full border border-slate-200 text-primary-600 hover:border-primary-500"><Shuffle class="h-3.5 w-3.5" /></RouterLink>
          <RouterLink :to="{ name: 'account' }" class="grid h-8 w-8 place-items-center rounded-full border border-slate-200 text-primary-600 hover:border-primary-500"><Heart class="h-3.5 w-3.5" /></RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
