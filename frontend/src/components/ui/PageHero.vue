<script setup>
import { computed } from 'vue';
import { ChevronRight } from 'lucide-vue-next';
import { heroImage } from '@/utils/media';

// items: [{ label, to? }] — last item is the current page.
const props = defineProps({
  title: { type: String, required: true },
  items: { type: Array, default: () => [] },
  image: { type: String, default: '' }
});

const bg = computed(() => props.image || heroImage('page-header', 1600, 400));
</script>

<template>
  <section class="page-hero" :style="{ backgroundImage: `url(${bg})` }">
    <div class="container relative text-center text-white">
      <h1 class="font-heading text-3xl font-black uppercase tracking-wide lg:text-4xl">{{ title }}</h1>
      <nav class="mt-3 flex items-center justify-center gap-1.5 text-sm">
        <RouterLink :to="{ name: 'home' }" class="text-white/80 hover:text-primary-400">{{ $t('nav.home') }}</RouterLink>
        <template v-for="(item, i) in items" :key="i">
          <ChevronRight class="h-4 w-4 text-white/50 rtl:rotate-180" />
          <RouterLink v-if="item.to && i < items.length - 1" :to="item.to" class="text-white/80 hover:text-primary-400">{{ item.label }}</RouterLink>
          <span v-else class="text-primary-400">{{ item.label }}</span>
        </template>
      </nav>
    </div>
  </section>
</template>
