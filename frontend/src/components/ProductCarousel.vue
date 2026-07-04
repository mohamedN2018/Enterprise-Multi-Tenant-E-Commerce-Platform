<script setup>
import { ref, computed } from 'vue';
import { ShoppingCart, Star, ChevronLeft, ChevronRight } from 'lucide-vue-next';
import { productImage, onImgError } from '@/utils/media';

const props = defineProps({
  title: { type: String, required: true },
  products: { type: Array, default: () => [] },
  addingId: { type: [String, Number, null], default: null }
});
const emit = defineEmits(['add']);

const scroller = ref(null);
const scrollBy = (amount) => scroller.value?.scrollBy({ left: amount, behavior: 'smooth' });

const img = (p) => p.image || p.images?.[0]?.image || productImage(p);
const price = (p) => p.price ?? p.min_price ?? p.display_price;
const currency = (p) => p.currency || p.store?.currency || '';
const rating = (p) => Math.round(Number(p.rating ?? p.average_rating ?? 0));

const list = computed(() => props.products.filter(Boolean));
</script>

<template>
  <section v-if="list.length" class="relative">
    <h2 class="section-title mb-4">{{ title }}</h2>

    <!-- Scroll arrows (desktop) -->
    <button
      type="button"
      class="absolute left-0 top-1/2 z-10 hidden h-10 w-10 -translate-y-1/2 place-items-center rounded-full border border-slate-200 bg-white text-ink shadow-card hover:bg-slate-50 md:grid dark:bg-slate-800"
      @click="scrollBy(-340)"
    >
      <ChevronLeft class="h-5 w-5" />
    </button>
    <button
      type="button"
      class="absolute right-0 top-1/2 z-10 hidden h-10 w-10 -translate-y-1/2 place-items-center rounded-full border border-slate-200 bg-white text-ink shadow-card hover:bg-slate-50 md:grid dark:bg-slate-800"
      @click="scrollBy(340)"
    >
      <ChevronRight class="h-5 w-5" />
    </button>

    <div ref="scroller" class="hero-scroll flex snap-x gap-4 overflow-x-auto pb-2 md:px-2">
      <div
        v-for="p in list"
        :key="p.id"
        class="flex w-[160px] shrink-0 snap-start flex-col rounded-xl border border-slate-200 bg-white transition hover:shadow-pop dark:border-slate-700 dark:bg-slate-800 sm:w-[180px]"
      >
        <RouterLink :to="{ name: 'product', params: { id: p.id } }" class="block overflow-hidden rounded-t-xl bg-lightbg">
          <img :src="img(p)" :alt="p.name" loading="lazy" class="aspect-square w-full object-cover transition duration-300 hover:scale-105" @error="onImgError" />
        </RouterLink>
        <div class="flex flex-1 flex-col p-3">
          <RouterLink :to="{ name: 'product', params: { id: p.id } }" class="clamp-2 min-h-[2.5rem] text-sm font-medium text-ink hover:text-primary-600">
            {{ p.name }}
          </RouterLink>
          <div class="mt-1 flex items-center gap-0.5">
            <Star v-for="n in 5" :key="n" class="h-3 w-3" :class="n <= rating(p) ? 'fill-amber-400 text-amber-400' : 'text-slate-300'" />
          </div>
          <p class="mt-1 font-heading text-base font-bold text-primary-600">{{ price(p) }} {{ currency(p) }}</p>
          <button class="btn btn-outline btn-sm mt-2 w-full" :disabled="addingId === p.id" @click="emit('add', p)">
            <ShoppingCart class="h-3.5 w-3.5" /> {{ addingId === p.id ? $t('product.adding') : $t('product.addToCart') }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
