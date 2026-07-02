<script setup>
import { computed } from 'vue';
import { ShoppingCart } from 'lucide-vue-next';
import StarRating from '@/components/ui/StarRating.vue';
import { productImage, onImgError } from '@/utils/media';

const props = defineProps({
  product: { type: Object, required: true },
  adding: { type: Boolean, default: false }
});
const emit = defineEmits(['add']);

const p = computed(() => props.product);
const img = computed(
  () => p.value.primary_image?.image || p.value.image || p.value.images?.[0]?.image || productImage(p.value)
);
const currency = computed(() => p.value.currency || p.value.store?.currency || '');
const price = computed(() => p.value.price ?? p.value.min_price ?? p.value.display_price);
const compareAt = computed(() => p.value.compare_at_price);
const onSale = computed(() => compareAt.value && Number(compareAt.value) > Number(price.value));
const rating = computed(() => Number(p.value.rating ?? p.value.average_rating ?? 0));
const reviews = computed(() => p.value.review_count ?? p.value.reviews_count ?? 0);
const storeName = computed(() => p.value.store?.name || p.value.store_name);
</script>

<template>
  <div class="card group flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:shadow-pop">
    <RouterLink :to="{ name: 'product', params: { id: p.id } }" class="relative block aspect-[4/3] overflow-hidden bg-slate-100">
      <img
        :src="img"
        :alt="p.name"
        loading="lazy"
        class="h-full w-full object-cover transition duration-300 group-hover:scale-105"
        @error="onImgError"
      />
      <span v-if="onSale" class="absolute left-3 top-3 rounded-md bg-rose-600 px-2 py-0.5 text-xs font-bold text-white">
        Sale
      </span>
    </RouterLink>

    <div class="flex flex-1 flex-col p-4">
      <p v-if="storeName" class="mb-1 text-xs font-medium text-primary-600">{{ storeName }}</p>
      <RouterLink
        :to="{ name: 'product', params: { id: p.id } }"
        class="clamp-2 font-semibold text-ink hover:text-primary-700"
      >
        {{ p.name }}
      </RouterLink>

      <div class="mt-1.5">
        <StarRating :value="rating" :count="reviews" :size="14" />
      </div>

      <div class="mt-3 flex items-end justify-between">
        <div>
          <span class="text-lg font-bold text-ink">{{ price }} {{ currency }}</span>
          <span v-if="onSale" class="ml-1.5 text-sm text-slate-400 line-through">{{ compareAt }}</span>
        </div>
        <button
          class="btn btn-primary btn-sm shrink-0"
          :disabled="adding"
          @click="emit('add', p)"
        >
          <ShoppingCart class="h-4 w-4" />
          <span class="hidden sm:inline">Add</span>
        </button>
      </div>
    </div>
  </div>
</template>
